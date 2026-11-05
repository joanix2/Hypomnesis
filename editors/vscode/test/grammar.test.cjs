const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { test, before } = require("node:test");
const { loadTokenizer, scoped } = require("./tokenize.cjs");

const root = path.resolve(__dirname, "../../..");
const grammarPath = path.join(__dirname, "../syntaxes/hypomnesis.tmLanguage.json");
const definition = JSON.parse(fs.readFileSync(grammarPath, "utf8"));
let tokenize;

before(async () => {
  tokenize = await loadTokenizer(grammarPath);
});

test("keywords exactly match alphabetic literals in the Lark grammar", () => {
  const lark = fs.readFileSync(path.join(root, "src/hypomnesis/language/grammar/hypomnesis.lark"), "utf8");
  const keywords = [...new Set([...lark.matchAll(/"([a-z]+)"/g)].map(match => match[1]))].sort();
  const match = definition.repository.keywords.match.match(/\(\?:([^)]*)\)/);
  assert.deepEqual(match[1].split("|").sort(), keywords);
});

test("nested and documentation comments keep their scopes across lines", () => {
  const tokens = tokenize("(** Description @interne\n (* imbrique *) suite\n *) let x = 1");
  assert(scoped(tokens, "comment.block.documentation.hypomnesis", "Description"));
  assert(scoped(tokens, "storage.type.annotation.hypomnesis", "@interne"));
  assert(scoped(tokens, "comment.block.hypomnesis", "imbrique"));
  assert(scoped(tokens, "comment.block.documentation.hypomnesis", "suite"));
  assert(scoped(tokens, "keyword.control.hypomnesis", "let"));
  assert(scoped(tokens, "constant.numeric.hypomnesis", "1"));
});

test("strings cannot introduce comments; escaped quotes stay in the string", () => {
  const tokens = tokenize('let s = "(* pas un commentaire *) \\" texte"');
  assert(scoped(tokens, "string.quoted.double.hypomnesis", "pas un commentaire"));
  assert(scoped(tokens, "constant.character.escape.hypomnesis", '\\"'));
  assert(!scoped(tokens, "comment.block.hypomnesis"));
});

test("types, booleans, numbers and operators are recognized", () => {
  const tokens = tokenize("type 'a t = Some of int\nlet x = 1_000.5e-2 +. 2.\nlet y = true");
  assert(scoped(tokens, "entity.name.type.variable.hypomnesis", "'a"));
  assert(scoped(tokens, "entity.name.type.hypomnesis", "Some"));
  assert(scoped(tokens, "entity.name.type.hypomnesis", "t"));
  assert(scoped(tokens, "storage.type.hypomnesis", "int"));
  assert(scoped(tokens, "constant.numeric.hypomnesis", "1_000.5e-2"));
  assert(scoped(tokens, "keyword.operator.hypomnesis", "+."));
  assert(scoped(tokens, "keyword.control.hypomnesis", "true"));
});

test("Python-style imports have keyword and namespace scopes", () => {
  const tokens = tokenize(
    "import physique.units as mesures\nfrom units import mm as millimetres\nopen mesures.Length",
  );
  for (const word of ["import", "from", "as", "open"]) {
    assert(scoped(tokens, "keyword.control.hypomnesis", word));
  }
  assert(scoped(tokens, "entity.name.namespace.hypomnesis", "physique.units"));
  assert(scoped(tokens, "entity.name.namespace.hypomnesis", "units"));
});

test("module signatures color contracts and abstract types", () => {
  const tokens = tokenize(
    "module type S = sig type t val make : int -> t end\nmodule M : S = struct type t = int end",
  );
  for (const word of ["module", "type", "sig", "val", "end", "struct"]) {
    assert(scoped(tokens, "keyword.control.hypomnesis", word));
  }
  assert(scoped(tokens, "entity.name.type.hypomnesis", "S"));
  assert(scoped(tokens, "entity.name.type.hypomnesis", "t"));
});

test("native language declarations highlight without a JSON manifest", () => {
  const tokens = tokenize('language exemple = struct let imports = ["../base"] let version = "1" end');
  assert(scoped(tokens, "keyword.control.hypomnesis", "language"));
  assert(scoped(tokens, "string.quoted.double.hypomnesis", "../base"));
});

test("the reported language declaration colors its name and metadata", () => {
  const tokens = tokenize(fs.readFileSync(path.join(__dirname, "fixtures/language.hyp"), "utf8"));
  for (const [scope, text] of [
    ["keyword.control.hypomnesis", "language"],
    ["entity.name.type.language.hypomnesis", "arithmetique"],
    ["variable.other.property.hypomnesis", "version"],
    ["variable.other.property.hypomnesis", "description"],
    ["string.quoted.double.hypomnesis", "1.0.0"],
    ["keyword.operator.hypomnesis", "="],
    ["keyword.control.hypomnesis", "struct"],
    ["keyword.control.hypomnesis", "let"],
    ["keyword.control.hypomnesis", "end"],
  ]) assert(scoped(tokens, scope, text), `${scope}: ${text}`);
});

test("nested metadata and multiline declarations stop at end, not a closing brace", () => {
  const tokens = tokenize([
    "language test",
    '= struct let procedure = { kind = "program"; entry = "version = end }" }',
    '(* description = end } *) let version = "1" end',
    'let normal = { version = "ordinary" }',
  ].join("\n"));
  assert(scoped(tokens, "variable.other.property.hypomnesis", "kind"));
  assert(scoped(tokens, "variable.other.property.hypomnesis", "entry"));
  assert(scoped(tokens[2], "variable.other.property.hypomnesis", "version"));
  assert(!scoped([tokens[3]], "meta.language.hypomnesis"));
  assert(!scoped([tokens[3]], "variable.other.property.hypomnesis"));
});

test("record keys and strings containing end do not close a language block", () => {
  const tokens = tokenize([
    'language test = struct let extra = { end = "end"; nested = [{value = true}] }',
    'let version = "1"',
    'end let normal = { version = "ordinary" }',
  ].join("\n"));
  assert(scoped(tokens[1], "variable.other.property.hypomnesis", "version"));
  const normal = tokens[2].filter(token => token.text.includes("version"));
  assert(normal.length);
  assert(!scoped([normal], "meta.language.hypomnesis"));
});

test("the removed record form does not receive metadata scopes", () => {
  const tokens = tokenize('language legacy = { version = "1" }\nlet x = 1');
  assert(!scoped(tokens, "variable.other.property.hypomnesis"));
  assert(!scoped([tokens[1]], "meta.language.hypomnesis"));
});

for (const name of ["mecanique/plaque.hyp", "ventilation/ventilation.hyp"]) {
  test(`real language ${name} has all expected scopes`, () => {
    const tokens = tokenize(fs.readFileSync(path.join(root, "demo", "languages", name), "utf8"));
    for (const scope of [
      "keyword.control.hypomnesis", "entity.name.type.hypomnesis",
      "string.quoted.double.hypomnesis", "constant.numeric.hypomnesis",
      "comment.block.documentation.hypomnesis",
    ]) {
      assert(scoped(tokens, scope), `missing ${scope}`);
    }
  });
}
