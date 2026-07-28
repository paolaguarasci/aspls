# aspls

VS Code / Cursor / VSCodium extension for Answer Set Programming (ASP-Core-2 / Clingo): **language intelligence** (diagnostics, completion, navigation, semantic highlighting) plus a **Clingo runner** (WASM or PATH) in one package.

Install from the [VS Marketplace](https://marketplace.visualstudio.com/items?itemName=pingflood.aspls) or [Open VSX](https://open-vsx.org/extension/pingflood/aspls).

**Repository:** https://github.com/paolaguarasci/aspls

The publishable extension lives in [`client/`](client/).

See [`client/README.md`](client/README.md) for features, settings, and maintainer publish notes (`publish:marketplace` / `publish:openvsx`). The **ASP → Solver** sidebar includes **Controls** for models, native Clingo path, and additional files (see Clingo config there).

## Pool semantics (LSP + runner)

Both the LSP server (`server/workspace_index.py :: resolve_pool`) and the client runner share the same canonical rules for determining which files are analysed together (the "pool"):

| `additionalFiles` in config | LSP pool                                                | Runner file set                          |
|-----------------------------|---------------------------------------------------------|------------------------------------------|
| Key absent / `null`         | Full workspace discovery (all `.lp` / `.asp` files)    | Active file only                         |
| `[]` (explicit empty array) | Active file only — no workspace fallback               | Active file only                         |
| `["a.lp", "b.lp"]`         | Active file + listed files                              | Active file + listed files               |

**Path resolution order** (per entry, both LSP and runner):
1. Relative to the active file's directory.
2. Relative to the workspace root (first folder).
3. If neither exists, the active-directory candidate is used as-is.

> **Note on `[]`**: an explicit empty array intentionally means "run/analyse the active file in isolation". It is _not_ treated as "no config" — that distinction prevents surprising cross-file symbol leakage.

### `additionalFiles` source of truth

| Source | Runtime effect |
|--------|----------------|
| `aspls.clingo.json` → `additionalFiles` | Canonical for LSP pool and Clingo runner |
| `aspls.clingo.additionalFiles` (Settings) | **Deprecated** — copied only when creating the config file (`aspls: Initialize Clingo config file` or Solver sidebar ensure); ignored at runtime |

This keeps LSP diagnostics and runner file sets aligned. Migrate by moving entries into `aspls.clingo.json` (or run **Initialize Clingo config file** to seed from your current setting).
