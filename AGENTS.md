# Release delivery

When delivering changes to cursor functionality, characters, assets, installers or Skills:

- Update `release/version.json`, release notes and usage instructions for the new version.
- Build the complete Windows ZIP with `release/build.ps1`; include all five themes, the local Web UI, recovery entries and both Skills. Exclude caches, nested old ZIPs, diagnostic screenshots and private credentials.
- Run checks appropriate to the change. Live Windows cursor tests must preserve the user's pre-test settings.
- Commit and push, then publish the matching version through `.github/workflows/release.yml` (a version tag or manual dispatch). Verify both the uploaded ZIP and checksum. Publishing a code commit alone does not finish a release update.
- Keep attachment filenames ASCII (`character-cursors-full-vX.Y.Z.zip`); Chinese filenames remain inside the package. Keep Vercel's full-download URL tied to `release/version.json`.
- Preserve prior releases and user backups. Update the README and online preview where user-facing behavior changes; keep them focused on public usage, not internal work logs.
