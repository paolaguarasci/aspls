# aspls — 5-minute video walkthrough (recording script)

Target duration: **~5 minutes**  
Audience: developers new to Answer Set Programming or aspls  
Prerequisites: VS Code, Cursor, or VSCodium; **Python 3** on PATH

Use this repo checked out locally so paths below match on screen.

| Act | Topic | Duration |
| --- | --- | --- |
| 1 | Install aspls | 0:00 – 1:15 |
| 2 | First answer set | 1:15 – 3:00 |
| 3 | Multi-file pool | 3:00 – 5:00 |

---

## Before recording

- [ ] Fresh editor window (no unrelated extensions cluttering the sidebar).
- [ ] Terminal closed or minimized — Python venv setup is automatic but noisy on first open.
- [ ] Zoom editor font to ~14–16 px so `.lp` syntax is readable on video.
- [ ] Open this folder: `aspls/` (repo root).
- [ ] Optional: install native [Clingo](https://potassco.org/clingo/) on PATH to demo config runs with real multi-file semantics; bundled WASM is enough for Acts 1–2.

---

## Act 1 — Install (0:00 – 1:15)

**On screen:** empty VS Code / Cursor window.

**Narration:**

> aspls brings Answer Set Programming to your editor: syntax highlighting, diagnostics, and a Clingo runner in one extension.

**Actions:**

1. Open **Extensions** (`Cmd+Shift+X` / `Ctrl+Shift+X`).
2. Search **`aspls`**.
3. Install **aspls — Answer Set Programming (Clingo)** by Paola Guarasci.
4. Click **Open Folder** and select the cloned `aspls` repo (or any empty folder for a clean demo).
5. Open `examples/01_basics/birds.lp`.

**On screen:** `birds.lp` with semantic highlighting (facts green, rule head blue, `#show` gold).

**Narration:**

> On first use, aspls starts a Python language server and creates a local venv — no manual setup beyond having Python 3 on your PATH.

**Tip:** If the status bar shows language-server activity, wait until diagnostics settle before Act 2.

---

## Act 2 — First answer set (1:15 – 3:00)

**On screen:** `examples/01_basics/birds.lp`.

**Narration:**

> This tiny program defines birds and penguins, then derives who can fly using default negation.

**Actions:**

1. Briefly scroll the file — point out `bird/1`, `penguin/1`, rule `flies(X)`, and `#show flies/1`.
2. Click the **play** icon in the editor title bar (**Compute first answer set**).
   - Alternative: Command Palette → `aspls: Compute first answer set`.
3. Activity Bar opens **ASP → Solver**.
4. Show the answer set, e.g. `{ flies(tweety) }` — `pingu` is a penguin, so `flies(pingu)` is not derived.
5. Click **All** (or run `aspls: Compute all answer sets`) — same single stable model here; mention that choice programs can yield many models.

**Narration:**

> Results stay in the Solver sidebar: models, errors, and re-run controls. No terminal required.

**Optional 10 s:** Hover `flies` or `bird` to show arity / occurrence hover from the language server.

---

## Act 3 — Multi-file pool (3:00 – 5:00)

**On screen:** switch to `examples/04_multi_file/rules.lp`.

**Narration:**

> Real projects split facts and rules across files. aspls uses a workspace config file as the single source of truth for which files belong to the **pool**.

**Actions:**

1. Open `examples/04_multi_file/aspls.clingo.json` side-by-side with `rules.lp`:

   ```json
   {
     "additionalFiles": ["facts.lp"]
   }
   ```

2. Explain: `rules.lp` is the active file; `facts.lp` is pulled in via `additionalFiles`.
3. Open `examples/04_multi_file/facts.lp` — show `bird/1` and `penguin/1` facts live here, not in `rules.lp`.
4. **Go to Definition** on `bird` in `rules.lp` → jumps to `facts.lp` (cross-file navigation).
5. Open **ASP → Predicates** — toggle **Show Workspace Predicates** to see symbols from the whole pool.
6. Run **`aspls: Compute answer sets (config)`** from the title bar or Solver **Config** button.
7. Confirm the same `{ flies(tweety) }` result — Clingo sees both files.

**Narration:**

> The same `aspls.clingo.json` drives the language server pool and the Clingo runner, so completion, go-to-definition, and solve all agree on which files matter. Create the file with **aspls: Initialize Clingo config file** in your own projects.

**Closing (~4:45 – 5:00):**

> Install from the Marketplace, open a `.lp` file, hit play, then add `additionalFiles` when your logic grows beyond one file. Links and tutorials are in the README.

**End card:** [VS Marketplace](https://marketplace.visualstudio.com/items?itemName=paolaguarasci.aspls) · [GitHub](https://github.com/paolaguarasci/aspls)

---

## Files referenced

| Path | Role in video |
| --- | --- |
| `examples/01_basics/birds.lp` | Single-file demo; first / all answer sets |
| `examples/04_multi_file/facts.lp` | Facts in the multi-file pool |
| `examples/04_multi_file/rules.lp` | Rules + `#show`; active file for config run |
| `examples/04_multi_file/aspls.clingo.json` | Pool config (`additionalFiles`) |

After recording, host the video (YouTube, etc.) and add the URL to the README **Video walkthrough** section.
