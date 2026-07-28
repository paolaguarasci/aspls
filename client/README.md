# aspls — Answer Set Programming (Clingo)

Language support for **Answer Set Programming** in the ASP-Core-2 / [Clingo](https://potassco.org/clingo/) dialect.

Works with **`.lp`** and **`.asp`** files in VS Code, Cursor, VSCodium, and other compatible editors.

**Why aspls:** one extension that combines **language intelligence** (diagnostics, completion, hover, go-to-definition / find-references, semantic + rainbow highlighting, optional learner mode) with a **Clingo runner** (bundled WASM or PATH binary, Solver sidebar). That avoids stacking a highlight-only extension (e.g. abelcour) with a separate run-oriented tool (e.g. Clingo for VSCode).

---

## Features

| Feature                      | What you get                                                                                                                                                                                                    |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Run Clingo**               | Compute first or all answer sets (editor title buttons, context menu, Command Palette)                                                                                                                          |
| **ASP sidebar — Solver**     | Activity Bar **ASP → Solver**: First / All / Config runs, answer sets, errors, re-run; **Controls** for models, native Clingo path, and additional files (persists to `aspls.clingo.json` / workspace settings) |
| **ASP sidebar — Predicates** | **ASP → Predicates**: active-file predicates nested by role → occurrence (powers **Outline**); toolbar toggle **Show Workspace Predicates** lists the Clingo pool or all workspace `.lp`/`.asp`                 |
| **PATH or WASM**             | Bundled `clingo-wasm` by default; optional Clingo binary from PATH                                                                                                                                              |
| **Syntax highlighting**      | Atoms, variables, comments, directives, operators                                                                                                                                                               |
| **Semantic highlighting**    | Different colors for facts, rule heads, rule bodies, constraints, `#show`, `#minimize`                                                                                                                          |
| **Rainbow predicates**       | Optional underline color per predicate name (stable across the file)                                                                                                                                            |
| **Diagnostics**              | Syntax errors from the ASP parser; optional Clingo-backed checks                                                                                                                                                |
| **IntelliSense**             | Predicate completion from the workspace / config file pool                                                                                                                                                      |
| **Hover**                    | Name, arity, occurrence counts; asp-lsp-style `%*…*%` docstrings; definition line + preceding comment                                                                                                           |
| **Go to Definition**         | Jump to facts and rule heads (cross-file)                                                                                                                                                                       |
| **Find References**          | All occurrences of a predicate in the pool                                                                                                                                                                      |
| **Learner mode**             | Optional rule-order and missing-comment warnings, plus **Fix Order** quick fix (off by default)                                                                                                                 |
| **Code Cookbook**            | Browse working ASP patterns (Command Palette / editor menu) and insert at cursor or open as a new `.lp` file                                                                                                    |
| **Snippets**                 | Typing templates for `#show`, `#const`, `#minimize`, aggregates, choice rules, weak constraints (distinct from the Cookbook)                                                                                    |

---

## Known limits (ASP grammar subset)

The language server parses a growing **subset** of Clingo / ASP-Core-2. Unsupported constructs get syntax diagnostics even when Clingo itself would accept them.

| Construct | Status |
|-----------|--------|
| Facts, rules, integrity constraints | Supported |
| Default negation (`not`) | Supported |
| Comparisons and `#count` / `#sum` / `#max` / `#min` | Supported |
| `#const`, `#show`, `#minimize` | Supported |
| Choice rules `{ … }` (optional INT bounds, `literal` / `literal : body`) | Supported |
| Weak constraints (`:~ … . [w@p, …]`) | Supported |
| `#maximize` | Not yet |
| `#include`, `#external`, `#heuristic`, `#script`, `#program` | Not yet |
| VARIABLE bounds on choice (`L { … } U` with variables) | Not yet |

Snippets and the Code Cookbook may show patterns ahead of the parser; prefer this table when diagnostics disagree with Clingo.

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

Workspace file `aspls.clingo.json` (name configurable via `aspls.clingo.configFile`) is the **canonical source** for `additionalFiles`, `models`, `threads`, and `customArgs` used by both the language server and the Clingo runner.

Create it with **aspls: Initialize Clingo config file**. If you already use `aspls.clingo.additionalFiles` in Settings, that value is **copied into the new file once** as a migration aid — it is not read at runtime anymore.

```json
{
  "models": 0,
  "threads": 1,
  "customArgs": "",
  "additionalFiles": ["facts.lp"]
}
```

Then run **aspls: Compute answer sets (config)**. Paths in `additionalFiles` are resolved relative to the active file, then the workspace root.

**Fallback when `additionalFiles` is absent from the config file:** the language server analyses all `.lp` / `.asp` files in the workspace. The runner includes only the active file unless you add an explicit `additionalFiles` array (use `[]` to run the active file in isolation).

Other `aspls.clingo.*` settings (`models`, `threads`, `customArgs`) still apply when the config file omits those keys. Only `additionalFiles` is config-file-only.

You can also edit **models**, **Use native Clingo** / **path**, and **additional files** from the Solver sidebar Controls section. Models and additional files write to the workspace config file; path settings write to workspace Settings. Threads and `customArgs` remain Settings / JSON only.

Before every run, aspls **preflights** the request: missing `additionalFiles`, invalid `models`, and a configured but missing `aspls.clingo.path` fail immediately in the Solver panel with an actionable message and a command summary that shows the effective backend (`WASM` or `PATH`).

### Capability matrix (WASM vs PATH)

| Feature | Bundled WASM | Native PATH |
|---------|--------------|-------------|
| Basic programs / answer sets | yes | yes |
| Multi-file via `additionalFiles` | limited (concatenated sources) | yes (real multi-file) |
| models / `-n` (via aspls UI) | yes | yes |
| `--const` / `-c` | yes | yes |
| Threads (`-t`) | limited | yes |
| Output control (`--outf`, `-q`, `--stats`, `--verbose`) | no | yes |
| Advanced CLI (`--parallel-mode`, `--configuration`, Lua, limits) | no | yes |

When WASM is active and `customArgs` include fragile flags, the Solver panel shows a **WASM capability warning** and suggests enabling `aspls.clingo.usePath`.

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

| Setting                        | Default             | Description                                                                                                       |
| ------------------------------ | ------------------- | ----------------------------------------------------------------------------------------------------------------- |
| `aspls.pythonPath`             | `""`                | Path to Python 3. Empty = auto-detect `python3` / `python`.                                                       |
| `aspls.rainbowPredicates`      | `true`              | Rainbow underline per predicate name (role colors stay from semantic highlighting).                               |
| `aspls.diagnostics.onceUsed`   | `true`              | Warn when a predicate appears only once (excluding `#show` / `#minimize`).                                        |
| `aspls.learnerMode`            | `false`             | Learner diagnostics: recommended construct order and missing preceding comments; enables **Fix Order** quick fix. |
| `aspls.clingo.usePath`         | `false`             | Use PATH / `aspls.clingo.path` instead of bundled WASM.                                                           |
| `aspls.clingo.path`            | `""`                | Optional absolute path to the Clingo binary.                                                                      |
| `aspls.clingo.models`          | `1`                 | Default model count for config runs (`0` = all).                                                                  |
| `aspls.clingo.threads`         | `1`                 | Clingo `-t` thread count.                                                                                         |
| `aspls.clingo.customArgs`      | `""`                | Extra CLI args (quoted tokens supported).                                                                         |
| `aspls.clingo.additionalFiles` | `[]`                | **Deprecated.** Migrated into `aspls.clingo.json` on init/ensure only; not used at runtime. |
| `aspls.clingo.configFile`      | `aspls.clingo.json` | Workspace config file name.                                                                                       |

Semantic highlighting for ASP is enabled by default (`editor.semanticHighlighting.enabled` for `[asp]`).

---

## Release checklist (stability B/D)

Before cutting a Marketplace / Open VSX build after pool or runner changes:

1. `npm test` in `client/` (includes B/D regression + WASM/PATH smoke).
2. `pytest` in `server/` (includes `additionalFiles=[]` pool regression).
3. Manual: set `additionalFiles: []` in `aspls.clingo.json` → onceUsed / hover stay file-local; remove the key → workspace pool returns.
4. Manual: add a missing path under `additionalFiles` → Solver shows preflight error (no hang).
5. Manual: WASM + `customArgs: "--outf=2"` → capability warning; enable `usePath` → warning gone.
6. Manual: edit `aspls.clingo.json` while a `.lp` is open → diagnostics refresh without reload window.

---

## Feedback

Issues and contributions: [github.com/paolaguarasci/aspls](https://github.com/paolaguarasci/aspls).

## License

MIT © Paola Guarasci
