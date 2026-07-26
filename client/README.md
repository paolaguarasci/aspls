# aspls — Answer Set Programming (Clingo)

Language support for **Answer Set Programming** in the ASP-Core-2 / [Clingo](https://potassco.org/clingo/) dialect.

Works with **`.lp`** and **`.asp`** files in VS Code, Cursor, VSCodium, and other compatible editors.

**Why aspls:** one extension that combines **language intelligence** (diagnostics, completion, hover, go-to-definition / find-references, semantic + rainbow highlighting, optional learner mode) with a **Clingo runner** (bundled WASM or PATH binary, Solver sidebar). That avoids stacking a highlight-only extension (e.g. abelcour) with a separate run-oriented tool (e.g. Clingo for VSCode).

---

## Features

| Feature | What you get |
|--------|----------------|
| **Run Clingo** | Compute first or all answer sets (editor title buttons, context menu, Command Palette) |
| **ASP sidebar — Solver** | Activity Bar **ASP → Solver**: First / All / Config runs, answer sets, errors, re-run; **Controls** for models, native Clingo path, and additional files (persists to `aspls.clingo.json` / workspace settings) |
| **ASP sidebar — Predicates** | **ASP → Predicates**: active-file predicates nested by role → occurrence (powers **Outline**); toolbar toggle **Show Workspace Predicates** lists the Clingo pool or all workspace `.lp`/`.asp` |
| **PATH or WASM** | Bundled `clingo-wasm` by default; optional Clingo binary from PATH |
| **Syntax highlighting** | Atoms, variables, comments, directives, operators |
| **Semantic highlighting** | Different colors for facts, rule heads, rule bodies, constraints, `#show`, `#minimize` |
| **Rainbow predicates** | Optional underline color per predicate name (stable across the file) |
| **Diagnostics** | Syntax errors from the ASP parser; optional Clingo-backed checks |
| **IntelliSense** | Predicate completion from the workspace / config file pool |
| **Hover** | Name, arity, occurrence counts; asp-lsp-style `%*…*%` docstrings; definition line + preceding comment |
| **Go to Definition** | Jump to facts and rule heads (cross-file) |
| **Find References** | All occurrences of a predicate in the pool |
| **Learner mode** | Optional rule-order and missing-comment warnings, plus **Fix Order** quick fix (off by default) |
| **Code Cookbook** | Browse working ASP patterns (Command Palette / editor menu) and insert at cursor or open as a new `.lp` file |
| **Snippets** | Typing templates for `#show`, `#const`, `#minimize`, aggregates, choice rules, weak constraints (distinct from the Cookbook) |

---

## Quick start

1. Install **aspls** from the [VS Marketplace](https://marketplace.visualstudio.com/items?itemName=pingflood.aspls) or [Open VSX](https://open-vsx.org/extension/pingflood/aspls) (Cursor / VSCodium).
2. Make sure **Python 3** is available on your PATH (or set `aspls.pythonPath`) for the language server.
3. Open a `.lp` file — the language server starts on first use and sets up a local venv automatically.
4. Click the **play** / **run all** icons in the editor title bar, or use the context menu / Command Palette:
   - **aspls: Compute first answer set**
   - **aspls: Compute all answer sets**
5. Results open in the Activity Bar **ASP → Solver** view (the sidebar focuses automatically after a run).

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

You can also edit **models**, **Use native Clingo** / **path**, and **additional files** from the Solver sidebar Controls section. Models and additional files write to the workspace config file; path settings write to workspace Settings. Threads and `customArgs` remain Settings / JSON only.

---

## Docstrings & learner mode

### Predicate docstrings (always on)

Document predicates with asp-lsp-style `%* … *%` blocks (anywhere in the file). Hover shows signature, description, and parameters; hovering an argument shows that parameter’s description.

```asp
%*
#bird(X).

A flying animal (unless it is a penguin).

#parameters
    - X : The individual.
*%

bird(tweety).
```

Without a formal docstring, hover still shows the **definition line** and any **preceding `%` comment**.

### Learner mode (`aspls.learnerMode`)

When enabled, the language server warns about:

1. **Rule order** — recommended: constants → facts → choices → definitions → constraints → optimization → show
2. **Missing preceding comments** — each statement should have a comment above it

On rule-order warnings, use **Quick Fix → Fix Order** to rewrite the file into the recommended order (comments stay attached to their statements).

---

## Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `aspls.pythonPath` | `""` | Path to Python 3. Empty = auto-detect `python3` / `python`. |
| `aspls.rainbowPredicates` | `true` | Rainbow underline per predicate name (role colors stay from semantic highlighting). |
| `aspls.diagnostics.onceUsed` | `true` | Warn when a predicate appears only once (excluding `#show` / `#minimize`). |
| `aspls.learnerMode` | `false` | Learner diagnostics: recommended construct order and missing preceding comments; enables **Fix Order** quick fix. |
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

- VS Code **1.85+** (or a compatible editor such as Cursor / VSCodium)
- **Python 3** (for the bundled language server: `pygls`, `lark`)
- Optional: **Clingo** on PATH when `aspls.clingo.usePath` is enabled

---

## Publishing (maintainers)

- **VS Marketplace:** `npm run publish:marketplace` (from repo root or `client/`; uses `vsce` / Azure DevOps PAT).
- **Open VSX** (Cursor / VSCodium): create an [Eclipse](https://accounts.eclipse.org/) account, sign the [Open VSX Publisher Agreement](https://open-vsx.org/user-settings/profile), generate a token, then once:

  ```bash
  npx ovsx create-namespace pingflood -p "$OVSX_PAT"
  ```

  Afterwards: `OVSX_PAT=… npm run publish:openvsx`

---

## Known limits

- Grammar covers a practical ASP-Core-2 / Clingo subset (facts, rules, constraints, aggregates, comparisons, common directives). Not every Clingo extension is parsed yet.
- Symbol index covers the workspace (all `.lp`/`.asp`) or, when `aspls.clingo.json` lists `additionalFiles`, that explicit file pool.
- `aspls.diagnostics.onceUsed` (default true) warns on predicates that appear only once in the pool.
- `aspls.learnerMode` (default false) adds pedagogy warnings; use Quick Fix **Fix Order** to auto-reorder.
- Bundled WASM supports common runs; some advanced CLI flags work more reliably with PATH Clingo.

---

## Feedback

Issues and contributions: [github.com/paolaguarasci/aspls](https://github.com/paolaguarasci/aspls).

## License

MIT © Paola Guarasci
