---
workflow: product-launch-video
flow: automation
storyboard: no
message: "ASP language intelligence and Clingo in one VS Code extension — install and solve"
destination: youtube
aspect: 1920x1080
language: en
length: 60s
angle: product-demo
audience: ASP students, researchers, and developers using VS Code or Cursor
voice: am_michael
---

## Intent

Sixty-second English promo for **aspls** — Answer Set Programming for VS Code, Cursor, and VSCodium. Sell the product: language intelligence plus a Clingo runner in one extension. Tone: clear, technical-confident, no hype fluff. Destination YouTube / embed (16:9). Offline build with Kokoro VO; no BGM (MusicGen unavailable).

## Assets

- Capture from https://github.com/paolaguarasci/aspls (README + brand signals).
- Local icon: ../../client/images/icon.png — extension icon for logo beats.

## Customizations

- Autonomous direct build (`storyboard: no`): skip sketch review; one preview at the end.
- Music: none (offline; MusicGen deps missing).
- TTS: Kokoro `am_michael` (male, EN).

## Notes

- Highlight: diagnostics, semantic highlighting, Clingo solve (WASM or PATH), Marketplace + Open VSX.
- Avoid inventing fake download counts; use real product claims from README.
- Do not scrape unrelated pages beyond the GitHub repo landing / README.
