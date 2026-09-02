# Standalone language server (Neovim, Emacs, Zed)

The **aspls** Python language server in [`server/`](../server/) speaks LSP over stdio. You can use it in any editor that supports custom language servers — without installing the VS Code extension.

The server provides parsing, diagnostics, completion, hover, go-to-definition, find-references, rename, document/workspace symbols, semantic tokens, inlay hints, code actions, formatting, and document links for **`.lp`** and **`.asp`** files.

> **VS Code–only features:** the Clingo runner, Solver sidebar, Code Cookbook, rainbow predicate decorations, and the custom `aspls/workspacePredicates` request are part of the TypeScript extension — not the standalone LSP.

## Prerequisites

- **Python 3.9+** (3.12+ recommended; CI tests 3.10–3.13)
- A clone of this repository (or a copy of the `server/` directory)

Optional: [Clingo](https://potassco.org/clingo/) on `PATH` enables extra Clingo-backed diagnostics when the server can find the binary.

## Install server dependencies

From the repository root:

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Dependencies: `pygls==1.3.1`, `lark==1.2.2` (see [`server/requirements.txt`](../server/requirements.txt)).

Verify the server starts (it reads JSON-RPC from stdin; exit with Ctrl+C):

```bash
PYTHONPATH=. python server.py
```

Note the absolute path to the venv Python and `server.py` — editors need both.

## Server command

All editors below use the same stdio command:

| Component | Example path |
| --- | --- |
| Python | `/path/to/aspls/server/.venv/bin/python` |
| Script | `/path/to/aspls/server/server.py` |

```bash
/path/to/aspls/server/.venv/bin/python /path/to/aspls/server/server.py
```

Set `PYTHONPATH` to the `server/` directory if your editor cannot inject environment variables and imports fail.

**Workspace root:** open your project folder (the directory containing `aspls.clingo.json` or `.git`). The server discovers `.lp` / `.asp` files under that root.

## Multi-file pool (`aspls.clingo.json`)

Create a workspace config file (same semantics as the VS Code extension):

```json
{
  "additionalFiles": ["facts.lp"]
}
```

| `additionalFiles` | LSP behaviour |
| --- | --- |
| Key absent | All `.lp` / `.asp` files in the workspace |
| `[]` | Active file only |
| `["a.lp", "b.lp"]` | Active file + listed files |

Paths resolve relative to the active file, then the workspace root. See the main [README](../readme.md#clingo-config) for full details.

## Optional LSP settings

The server reads VS Code–compatible settings from `workspace/didChangeConfiguration`. Editors that support `settings` in their LSP client can pass:

```json
{
  "aspls": {
    "learnerMode": false,
    "diagnostics": {
      "onceUsed": true
    },
    "clingo": {
      "configFile": "aspls.clingo.json"
    }
  }
}
```

| Setting | Default | Effect |
| --- | --- | --- |
| `aspls.learnerMode` | `false` | Rule-order and comment hints + quick fixes |
| `aspls.diagnostics.onceUsed` | `true` | Warn on single-use body predicates |
| `aspls.clingo.configFile` | `aspls.clingo.json` | Config file name for `additionalFiles` |

If your editor does not send configuration, defaults apply and the pool still comes from `aspls.clingo.json` on disk.

---

## Neovim

Requires **Neovim 0.10+** (0.11+ recommended for built-in `vim.lsp.config`).

Add to `init.lua` (adjust paths):

```lua
vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'lp', 'asp' },
  callback = function(args)
    vim.lsp.start({
      name = 'aspls',
      cmd = {
        '/path/to/aspls/server/.venv/bin/python',
        '/path/to/aspls/server/server.py',
      },
      root_dir = vim.fs.root(args.buf, { 'aspls.clingo.json', '.git' }),
      capabilities = vim.lsp.protocol.make_client_capabilities(),
    })
  end,
})
```

**Filetype detection** — Neovim does not ship `.lp` / `.asp` filetypes. Add to `init.lua`:

```lua
vim.filetype.add({
  extension = {
    lp = 'lp',
    asp = 'asp',
  },
})
```

**Semantic tokens** — enable if your colorscheme supports LSP semantic highlighting:

```lua
vim.api.nvim_create_autocmd('LspAttach', {
  callback = function(args)
    if vim.lsp.get_client_by_id(args.data.client_id).name == 'aspls' then
      vim.lsp.semantic_tokens.enable(true, args.buf)
    end
  end,
})
```

**Check:** `:LspInfo` should list `aspls` when a `.lp` buffer is open. Hover and diagnostics should appear on [`examples/01_basics/birds.lp`](../examples/01_basics/birds.lp).

---

## Emacs

Requires **Eglot** (built into Emacs 29+) or **lsp-mode**.

### Eglot (recommended)

```elisp
;; ~/.emacs.d/init.el
(add-to-list 'auto-mode-alist '("\\.lp\\'" . lp-mode))
(add-to-list 'auto-mode-alist '("\\.asp\\'" . asp-mode))

(define-derived-mode lp-mode prog-mode "LP"
  "Major mode for Answer Set Programming (.lp files).")

(add-to-list 'eglot-server-programs
             '((lp-mode asp-mode) . ("/path/to/aspls/server/.venv/bin/python"
                                      "/path/to/aspls/server/server.py")))
```

Open a `.lp` file, then `M-x eglot` (or enable `eglot-ensure`).

### lsp-mode

```elisp
(require 'lsp-mode)

(add-to-list 'auto-mode-alist '("\\.lp\\'" . lp-mode))
(define-derived-mode lp-mode prog-mode "LP" "ASP (.lp)")

(lsp-register-client
 (make-lsp-client
  :new-connection (lsp-stdio-connection
                  '("/path/to/aspls/server/.venv/bin/python"
                    "/path/to/aspls/server/server.py"))
  :major-modes '(lp-mode)
  :server-id 'aspls
  :priority 1))
```

**Check:** `M-x eglot-events-buffer` (or `lsp-workspace-folders`) should show the project root. Diagnostics appear in `M-x flymake-mode` / `M-x flycheck`.

---

## Zed

Zed registers language servers through **extensions** — you cannot point at an arbitrary binary in `settings.json` alone. Two practical options:

### Option A — zed-customlsp (fastest)

1. Install the [zed-customlsp](https://github.com/zhcn000000/zed-customlsp) dev extension in Zed.
2. Add an aspls entry to its `extension.toml`:

```toml
[language_servers.aspls]
name = "aspls"
languages = ["ASP"]
```

3. Reinstall/reload the extension, then add to `~/.config/zed/settings.json`:

```json
{
  "file_types": {
    "ASP": ["lp", "asp"]
  },
  "languages": {
    "ASP": {
      "language_servers": ["aspls"],
      "semantic_tokens": "full"
    }
  },
  "lsp": {
    "aspls": {
      "binary": {
        "path": "/path/to/aspls/server/.venv/bin/python",
        "arguments": ["/path/to/aspls/server/server.py"]
      },
      "settings": {
        "aspls": {
          "diagnostics": { "onceUsed": true },
          "learnerMode": false
        }
      }
    }
  }
}
```

Replace the paths with your venv Python and `server.py`. **Restart Zed** after changing LSP settings.

> If Zed reports “no language server found matching aspls”, reload the zed-customlsp extension so it picks up the new `extension.toml` entry.

### Option B — full Zed extension

For syntax highlighting, outlines, and first-class `.lp` support, ship a proper Zed language extension with a Tree-sitter grammar, `languages/asp/config.toml`, and a `language_server_command` implementation. See [Zed: Language Extensions](https://zed.dev/docs/extensions/languages) and the official `language_server_command` API:

```rust
Ok(zed::Command {
    command: "/path/to/aspls/server/.venv/bin/python".into(),
    args: vec!["/path/to/aspls/server/server.py".into()],
    env: Default::default(),
})
```

An official aspls Zed extension may be published separately; until then, Option A covers diagnostics, completion, hover, and navigation via LSP alone.

**Check:** open [`examples/01_basics/birds.lp`](../examples/01_basics/birds.lp), then **Zed → Help → Open Log** — the aspls server should start without import errors.

---

## Supported LSP capabilities

| Capability | Standalone LSP |
| --- | --- |
| Diagnostics (syntax + optional Clingo) | yes |
| Hover, completion, signature help | yes |
| Go to definition / references / rename | yes |
| Document + workspace symbols | yes |
| Semantic tokens | yes |
| Inlay hints, code lens, code actions | yes |
| Document formatting, document links | yes |
| Clingo run / Solver UI | VS Code extension only |
| Code Cookbook, rainbow decorations | VS Code extension only |
| `aspls/workspacePredicates` (Predicates tree) | VS Code extension only |

Grammar coverage table: [README § Grammar coverage](../readme.md#grammar-coverage).

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ModuleNotFoundError: pygls` | Activate the venv or reinstall `requirements.txt` |
| No cross-file symbols | Add `aspls.clingo.json` with `additionalFiles`, or open the workspace root |
| Server exits immediately | Ensure the editor uses **stdio**, not socket/TCP |
| Zed: “no language server found” | Install/reload the dev extension; restart Zed after changing LSP settings |

For development and tests, see [README § Development](../readme.md#development).
