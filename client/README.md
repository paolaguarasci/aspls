# aspls — Answer Set Programming (Clingo)

Language support for **Answer Set Programming** in the ASP-Core-2 / [Clingo](https://potassco.org/clingo/) dialect.

Works with **`.lp`** and **`.asp`** files in VS Code (and compatible editors).

---

## Features

| Feature | What you get |
|--------|----------------|
| **Run Clingo** | Compute first or all answer sets (editor title buttons, context menu, Command Palette) |
| **Results panel** | Dedicated **ASP → Results** view: readable/copyable answer sets, errors, re-run |
| **PATH or WASM** | Bundled `clingo-wasm` by default; optional Clingo binary from PATH |
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
2. Make sure **Python 3** is available on your PATH (or set `aspls.pythonPath`) for the language server.
3. Open a `.lp` file — the language server starts on first use and sets up a local venv automatically.
4. Click the **play** / **run all** icons in the editor title bar, or use the context menu / Command Palette:
   - **aspls: Compute first answer set**
   - **aspls: Compute all answer sets**
5. Results open in the **ASP** panel tab.

Optional: install [Clingo](https://potassco.org/clingo/) on PATH for extra diagnostics (grounding/safety) and to use the system solver via `aspls.clingo.usePath`.

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

## Clingo config

Settings under `aspls.clingo.*` control models, threads, `customArgs`, and `additionalFiles`.

For multi-file programs and shared flags, create a workspace file (default name `aspls.clingo.json`) with:

**aspls: Initialize Clingo config file**

```json
{
  "models": 0,
  "threads": 1,
  "customArgs": "",
  "additionalFiles": ["facts.lp"]
}
```

Then run **aspls: Compute answer sets (config)**. Paths in `additionalFiles` are resolved relative to the active file, then the workspace root.

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `aspls.pythonPath` | `""` | Path to Python 3. Empty = auto-detect `python3` / `python`. |
| `aspls.rainbowPredicates` | `true` | Rainbow underline per predicate name (role colors stay from semantic highlighting). |
| `aspls.clingo.usePath` | `false` | Use PATH / `aspls.clingo.path` instead of bundled WASM. |
| `aspls.clingo.path` | `""` | Optional absolute path to the Clingo binary. |
| `aspls.clingo.models` | `1` | Default model count for config runs (`0` = all). |
| `aspls.clingo.threads` | `1` | Clingo `-t` thread count. |
| `aspls.clingo.customArgs` | `""` | Extra CLI args (quoted tokens supported). |
| `aspls.clingo.additionalFiles` | `[]` | Extra program files to include. |
| `aspls.clingo.configFile` | `aspls.clingo.json` | Workspace config file name. |

Semantic highlighting for ASP is enabled by default (`editor.semanticHighlighting.enabled` for `[asp]`).

---

## Requirements

- VS Code **1.85+** (or a compatible editor)
- **Python 3** (for the bundled language server: `pygls`, `lark`)
- Optional: **Clingo** on PATH when `aspls.clingo.usePath` is enabled

---

## Known limits

- Grammar covers a practical ASP-Core-2 / Clingo subset (facts, rules, constraints, aggregates, comparisons, common directives). Not every Clingo extension is parsed yet.
- Diagnostics and navigation are **per document** (not whole workspace project graphs).
- Bundled WASM supports common runs; some advanced CLI flags work more reliably with PATH Clingo.

---

## Feedback

Issues and contributions: [github.com/paolaguarasci/aspls](https://github.com/paolaguarasci/aspls).

## License

MIT © Paola Guarasci
