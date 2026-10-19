# Changelog

All notable changes to **aspls** are documented in this file.

## [0.8.1] — 2026-10-19

### Security
- `aspls.pythonPath` and `aspls.clingo.path` can no longer be set by a workspace (`.vscode/settings.json`). Both name an executable, so an untrusted project could have made the extension run a program of its choice. They are now machine-scoped, restricted in untrusted workspaces, and read from user settings only.

### Changed
- The Solver sidebar saves the chosen Clingo binary to user settings instead of workspace settings, so the choice applies to every project.
- The extension declares limited support for untrusted workspaces.

### Publishing
- Open VSX: `0.8.1` (namespace `pingflood`)
- GitHub release: `v0.8.1`

## [0.8.0] — 2026-10-06

### Added
- Teaching tutorials under `examples/`: weak constraints (`05_weak_constraint`), graph coloring (`06_graph_coloring`), and N-Queens (`07_nqueens`).
- Code Cookbook recipes for N-Queens, guess-and-check schema, and graph reachability (lab-oriented patterns).
- README **Impact** section with Marketplace / Open VSX download stats and walkthrough pointer.
- DAP grounding debug adapter (step through Clingo grounding) from the 0.7.x development line.

### Changed
- Open VSX install links and badges point to the published namespace `pingflood/aspls` (Marketplace remains `paolaguarasci.aspls`).
- Learning-path table in the README covers the new tutorials.

### Publishing
- VS Marketplace and Open VSX: `0.8.0`
- GitHub release: `v0.8.0`

## [0.7.1] — 2026-09-02

- Open VSX publish of `0.7.1` (publisher namespace `pingflood`).
- Publish helper script for Open VSX (`client/scripts/publish-openvsx.sh`).

## [0.7.0] — 2026-09-02

- VS Marketplace publish of `0.7.0`.
- Solver sidebar, multi-file pool, cookbook, learner mode, and WASM/PATH Clingo runner as documented in the README.
