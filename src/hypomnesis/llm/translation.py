"""Natural language → M1 program in an M2 language, by an LLM (cahier des charges §14).

The LLM only translates. Its output is a candidate program that the engine
parses and type-checks; on failure the compiler's diagnostic is sent back for
a bounded number of repairs (§14.3). Nothing it writes runs before that.

The prompt is built from the language itself (its Hypomnesis sources and the
entry point named by its manifest) and from example M1 programs: no domain
knowledge lives here.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from hypomnesis.engine.language import Language, load_language
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.llm.describe import catalogue
from hypomnesis.llm.ollama import Reply
from hypomnesis.llm.prompting import DEFAULT, Strategy
from hypomnesis.llm.retrieval import Retriever, load_examples

SYSTEM = """Tu traduis une demande en français en un programme Hypomnesis.
Hypomnesis a la syntaxe d'OCaml : `let x = …`, records `{ Module.champ = …; autre = … }`,
listes `[a; b]`, options `Some x` / `None`, flottants avec un point (`120.0`), chaînes entre
guillemets droits. Le programme est écrit dans le langage métier défini ci-dessous.

Règles :
- Tu ne fais que traduire. Tu ne calcules rien que le langage calcule lui-même.
- N'invente aucune valeur : si une information est absente de la demande et que le type le
  permet, elle reste inconnue (`None`). Si le type l'exige, prends la valeur indiquée par les
  commentaires du langage ou des exemples.
- Exprime les grandeurs dans les unités du langage (indiquées en commentaire) : convertis
  centimètres, mètres, grammes si nécessaire.
- Le programme doit définir `let {entry} = …` en appelant une procédure du langage
  (une valeur de type `… Effect.t`).
- Réponds uniquement par le code du programme, sans explication ni balises Markdown."""


class ChatClient(Protocol):
    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        num_ctx: int = ...,
        temperature: float = ...,
    ) -> Reply: ...


@dataclass
class Attempt:
    program: str
    reply: Reply
    error: str = ""  # diagnostic du compilateur ou de la simulation, vide si accepté
    stage: str = ""  # "syntax error", "type error", "runtime error", …


@dataclass
class Translation:
    request: str
    attempts: list[Attempt] = field(default_factory=list)

    @property
    def compiled(self) -> bool:
        return bool(self.attempts) and self.attempts[-1].stage in ("", "runtime error")

    @property
    def accepted(self) -> bool:
        return bool(self.attempts) and not self.attempts[-1].error

    @property
    def program(self) -> str:
        return self.attempts[-1].program if self.attempts else ""


def extract_code(text: str) -> str:
    """Le code, sans balises Markdown ni réflexion éventuelle.

    Certains modèles raisonnent malgré la consigne et ferment leur réflexion par
    `</think>`, parfois sans balise ouvrante : seul ce qui suit compte."""
    if "</think>" in text:
        text = text.rsplit("</think>", 1)[1]
    fenced = re.findall(r"```[a-zA-Z]*\n(.*?)```", text, flags=re.S)
    return (fenced[0] if fenced else text).strip() + "\n"


def system_prompt(language: Language, examples: list[str], strategy: Strategy = DEFAULT) -> str:
    parts = [SYSTEM.replace("{entry}", language.procedure["entry"])]
    published = catalogue(language) if strategy.catalogue else None
    # A language that documents nothing has no catalogue: fall back on its source.
    if strategy.source or (published is not None and not published.modules):
        sources = "\n\n".join(
            (language.root / s).read_text(encoding="utf-8") for s in language.manifest["sources"]
        )
        parts.append(f"=== Langage « {language.name} » ===\n{sources}")
    if published is not None and published.modules:
        parts.append(published.render())
    if strategy.programs:
        for i, example in enumerate(examples, 1):
            parts.append(f"=== Exemple de programme {i} ===\n{example}")
    return "\n\n".join(parts)


def shots(language: Language, request: str, strategy: Strategy) -> list[dict[str, str]]:
    """Worked examples as alternating user / assistant turns (the closest one last)."""
    worked = load_examples(language)
    chosen = (
        Retriever(worked).top(request, strategy.shots)
        if strategy.retrieval
        else worked[: strategy.shots]
    )
    turns: list[dict[str, str]] = []
    for example in chosen:
        turns += [
            {"role": "user", "content": example.request},
            {"role": "assistant", "content": example.program.strip()},
        ]
    return turns


def check(language_root: Path, program: str) -> tuple[str, str]:
    """Charge le programme dans une session neuve du langage : ("", "") s'il est accepté."""
    language = load_language(language_root)
    entry = language.procedure["entry"]
    try:
        language.load_program(program)
        if not language.session.type_of(entry).endswith("Effect.t"):
            return "type error", f"`{entry}` doit être une procédure (type … Effect.t)"
    except HypomnesisError as exc:
        if exc.stage == "name error" and f"unbound value {entry}" in exc.message:
            return exc.stage, (
                f"`{entry}` n'est pas défini : le programme doit se terminer par "
                f"`let {entry} = …` qui appelle une procédure du langage."
            )
        return exc.stage, exc.render(program, "<programme>")
    return "", ""


_PROGRAM_START = re.compile(r"\s*(let|module|open|type|external|\(\*)\b|\s*\(\*")


def repair_message(stage: str, error: str, program: str) -> str:
    """The feedback sent to the model: diagnostic, then what to do about it."""
    if stage == "runtime error":
        return (
            f"Le programme est accepté par le compilateur mais échoue à l'exécution "
            f"(simulation) :\n{error}\n"
            "Choisis une autre procédure du langage, ou une autre façon de l'appeler, "
            "qui produit elle-même les faits dont l'étape fautive a besoin. "
            "Renvoie uniquement le programme complet."
        )
    prose = stage == "syntax error" and not _PROGRAM_START.match(program)
    hint = (
        "Ta réponse n'est pas un programme : elle commence par du texte. Renvoie uniquement "
        "le code du programme, sans réflexion ni explication."
        if prose
        else "Corrige-le et renvoie uniquement le programme complet."
    )
    return f"Le compilateur refuse ce programme :\n{error}\n{hint}"


def translate(
    client: ChatClient,
    model: str,
    language: Language,
    request: str,
    *,
    examples: list[str],
    max_repairs: int = 2,
    simulate: Callable[[str], str] | None = None,
    strategy: Strategy = DEFAULT,
    temperature: float = 0.0,
) -> Translation:
    messages = [
        {"role": "system", "content": system_prompt(language, examples, strategy)},
        *shots(language, request, strategy),
        {"role": "user", "content": request},
    ]
    result = Translation(request)
    for _ in range(max_repairs + 1):
        reply = client.chat(model, messages, temperature=temperature)
        program = extract_code(reply.text)
        stage, error = check(language.root, program)
        if not error and simulate is not None:
            error = simulate(program)  # dry-run failure, "" if the program runs
            stage = "runtime error" if error else ""
        result.attempts.append(Attempt(program, reply, error, stage))
        if not error:
            break
        messages += [
            {"role": "assistant", "content": reply.text},
            {"role": "user", "content": repair_message(stage, error, program)},
        ]
    return result
