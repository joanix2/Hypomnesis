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
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from hypomnesis.engine.language import Language, load_language
from hypomnesis.language.errors import HypomnesisError
from hypomnesis.llm.ollama import Reply

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
    def chat(self, model: str, messages: list[dict[str, str]], *, num_ctx: int = ...) -> Reply: ...


@dataclass
class Attempt:
    program: str
    reply: Reply
    error: str = ""  # diagnostic du compilateur, vide si accepté
    stage: str = ""  # "syntax error", "type error", …


@dataclass
class Translation:
    request: str
    attempts: list[Attempt] = field(default_factory=list)

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


def system_prompt(language: Language, examples: list[str]) -> str:
    sources = "\n\n".join(
        (language.root / s).read_text(encoding="utf-8") for s in language.manifest["sources"]
    )
    parts = [
        SYSTEM.replace("{entry}", language.procedure["entry"]),
        f"=== Langage « {language.name} » ===\n{sources}",
    ]
    for i, example in enumerate(examples, 1):
        parts.append(f"=== Exemple de programme {i} ===\n{example}")
    return "\n\n".join(parts)


def check(language_root: Path, program: str) -> tuple[str, str]:
    """Charge le programme dans une session neuve du langage : ("", "") s'il est accepté."""
    language = load_language(language_root)
    try:
        language.load_program(program)
        entry = language.procedure["entry"]
        if not language.session.type_of(entry).endswith("Effect.t"):
            return "type error", f"`{entry}` doit être une procédure (type … Effect.t)"
    except HypomnesisError as exc:
        return exc.stage, exc.render(program, "<programme>")
    return "", ""


def translate(
    client: ChatClient,
    model: str,
    language: Language,
    request: str,
    *,
    examples: list[str],
    max_repairs: int = 2,
) -> Translation:
    messages = [
        {"role": "system", "content": system_prompt(language, examples)},
        {"role": "user", "content": request},
    ]
    result = Translation(request)
    for _ in range(max_repairs + 1):
        reply = client.chat(model, messages)
        program = extract_code(reply.text)
        stage, error = check(language.root, program)
        result.attempts.append(Attempt(program, reply, error, stage))
        if not error:
            break
        messages += [
            {"role": "assistant", "content": reply.text},
            {
                "role": "user",
                "content": f"Le compilateur refuse ce programme :\n{error}\n"
                "Corrige-le et renvoie uniquement le programme complet.",
            },
        ]
    return result
