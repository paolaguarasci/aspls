# aspls — Answer Set Programming (Clingo)

Language support for **Answer Set Programming** in the ASP-Core-2 / [Clingo](https://potassco.org/clingo/) dialect.

Works with **`.lp`** and **`.asp`** files in VS Code (and compatible editors).

---

## Features

| Feature | What you get |
|--------|----------------|
| **Syntax highlighting** | Atoms, variables, comments, directives, operators |
| **Semantic highlighting** | Different colors for facts, rule heads, rule bodies, constraints, `#show`, `#minimize` |
| **Rainbow predicates** | Optional underline color per predicate name (stable across the file) |
| **Diagnostics** | Syntax errors from the ASP parser; optional Clingo-backed checks |
| **IntelliSense** | Predicate completion from the current document |
| **Hover** | Name, arity, and head/body occurrence counts |
| **Go to Definition** | Jump to facts and rule heads |
| **Find References** | All occurrences of a predicate in the file |

---

## Quick start

1. Install **aspls** from the Marketplace.
2. Make sure **Python 3** is available on your PATH (or set `aspls.pythonPath`).
3. Open a `.lp` file — the language server starts on first use and sets up a local venv automatically.

Optional: install [Clingo](https://potassco.org/clingo/) for extra diagnostics.

---

## Example

```asp
% Birds that are not penguins can fly
bird(tweety).
penguin(pingu).

flies(X) :- bird(X), not penguin(X).

#show flies/1.
```

- **Facts** (`bird`, `penguin`) — bold green  
- **Rule head** (`flies`) — bold blue  
- **Rule body** — muted; `not penguin` italic when negated  
- **`#show`** — gold  

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `aspls.pythonPath` | `""` | Path to Python 3. Empty = auto-detect `python3` / `python`. |
| `aspls.rainbowPredicates` | `true` | Rainbow underline per predicate name (role colors stay from semantic highlighting). |

Semantic highlighting for ASP is enabled by default (`editor.semanticHighlighting.enabled` for `[asp]`).

---

## Requirements

- VS Code **1.85+** (or a compatible editor)
- **Python 3** (for the bundled language server: `pygls`, `lark`)
- Optional: **Clingo** on PATH for additional checks

---

## Known limits

- Grammar covers a practical ASP-Core-2 / Clingo subset (facts, rules, constraints, aggregates, comparisons, common directives). Not every Clingo extension is parsed yet.
- Diagnostics and navigation are **per document** (not whole workspace project graphs).

---

## Feedback

Issues and contributions: [github.com/paolaguarasci/aspls](https://github.com/paolaguarasci/aspls).

## License

MIT © Paola Guarasci
