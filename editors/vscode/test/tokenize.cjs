const fs = require("node:fs");
const textmate = require("vscode-textmate");
const oniguruma = require("vscode-oniguruma");

exports.loadTokenizer = async grammarPath => {
  const wasm = fs.readFileSync(require.resolve("vscode-oniguruma/release/onig.wasm"));
  await oniguruma.loadWASM(wasm);
  const definition = JSON.parse(fs.readFileSync(grammarPath, "utf8"));
  const registry = new textmate.Registry({
    onigLib: Promise.resolve({
      createOnigScanner: patterns => new oniguruma.OnigScanner(patterns),
      createOnigString: source => new oniguruma.OnigString(source),
    }),
    loadGrammar: async () => definition,
  });
  const grammar = await registry.loadGrammar("source.hypomnesis");
  return source => {
    let state = textmate.INITIAL;
    return source.split("\n").map(line => {
      const result = grammar.tokenizeLine(line, state);
      state = result.ruleStack;
      return result.tokens.map(token => ({
        text: line.slice(token.startIndex, token.endIndex),
        scopes: token.scopes,
      }));
    });
  };
};

exports.scoped = (tokens, scope, text) => tokens.flat().some(token =>
  token.scopes.includes(scope) && (text === undefined || token.text.includes(text)),
);
