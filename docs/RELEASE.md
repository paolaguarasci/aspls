# Release checklist — aspls v0.8.0

## Before publish

- [ ] `cd server && pytest -q`
- [ ] `cd client && npm test`
- [ ] New tutorials solve with Clingo (`examples/05_*` … `07_*`)
- [ ] CHANGELOG.md entry for `0.8.0` is accurate
- [ ] `client/package.json` version is `0.8.0`

## Publish

```bash
# from repo root
npm run package                 # builds .vsix in client/
npm run publish:marketplace     # requires vsce login (publisher paolaguarasci)
```

**Open VSX (preferred):** GitHub → Actions → **Publish Open VSX** → Run workflow  
(OIDC trusted publisher; workflow [`.github/workflows/publish-openvsx.yml`](../.github/workflows/publish-openvsx.yml). No `OVSX_PAT`.)

**Open VSX (manual fallback):**

```bash
OVSX_PAT=… npm run publish:openvsx   # publisher pingflood via script
```

## GitHub release

```bash
git tag -a v0.8.0 -m "aspls 0.8.0"
git push origin main --tags
gh release create v0.8.0 --title "aspls 0.8.0" --notes-file CHANGELOG.md
```

Attach the `.vsix`. Overview clip: [`docs/media/aspls-overview.mp4`](media/aspls-overview.mp4). Optional 4K master stays local under `videos/aspls-promo/renders/`.

## After publish

- [ ] Confirm Marketplace shows `0.8.0`
- [ ] Confirm Open VSX shows `0.8.0` under `pingflood/aspls`
- [ ] Update README Impact table numbers (optional, after a few days)
- [ ] Confirm README overview still / poster + MP4 link work on github.com
