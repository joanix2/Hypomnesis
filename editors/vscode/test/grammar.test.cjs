const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { test, before } = require("node:test");
const textmate = require("vscode-textmate");
const oniguruma = require("vscode-oniguruma");

const root = path.resolve(__dirname, "../../..");
const grammarPath = path.join(__dirname, "../syntaxes/hypomnesis.tmLanguage.json");
const definition = JSON.parse(fs.readFileSync(grammarPath, "utf8"));
let grammar;

before(async () => {
  const wasm = fs.readFileSync(require.resolve("vscode-oniguruma/release/onig.wasm"));
  await oniguruma.loadWASM(wasm);
  const registry = new textmate.Registry({
    onigLib: Promise.resolve({
      createOnigScanner: patterns => new oniguruma.OnigScanner(patterns),
      createOnigString: source => new oniguruma.OnigString(source),
    }),
    loadGrammar: async () => definition,
  });
  grammar = await registry.loadGrammar("source.hypomnesis");
});

function tokenize(source) {
  let state = textmate.INITIAL;
  return source.split("\n").map(line => {
    const result = grammar.tokenizeLine(line, state);
    state = result.ruleStack;
    return result.tokens.map(token => ({
      text: line.slice(token.startIndex, token.endIndex),
      scopes: token.scopes,
    }));
  });
}

function scoped(tokens, scope, text) {
  return tokens.flat().some(token =>
    token.scopes.includes(scope) && (text === undefined || token.text.includes(text)),
  );
}

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
