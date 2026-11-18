# Packaging

What is published where, and what to do on each release `vX.Y.Z`.

| Channel | Source of truth | Status |
|---------|-----------------|--------|
| GitHub Release (AppImage, .deb, .rpm, Windows setup/.msi, macOS .dmg) | `.github/workflows/desktop-release.yml` on a `v*` tag (draft) | works |
| Homebrew cask | `packaging/homebrew/lunar-eval.rb` copied to a tap repo `Pedrojonfg/homebrew-clps` | template, tap repo not created |
| winget | `packaging/winget/*.yaml`, submitted to `microsoft/winget-pkgs` | template, not submitted |

## Per release

1. Push tag `vX.Y.Z`. Wait for the workflow. Check the draft release has all installers, edit the notes from `docs/RELEASE_NOTES_TEMPLATE.md`, publish it.
2. Hashes: `sha256sum lunar-eval_X.Y.Z_aarch64.dmg lunar-eval_X.Y.Z_x64-setup.exe`.
3. Homebrew: put the version and dmg sha256 in the cask, push it to the tap as `Casks/lunar-eval.rb`. Test with `brew install --cask Pedrojonfg/clps/lunar-eval`.
4. winget: fill the version, URL and installer sha256 in the three YAML files, `winget validate`, then PR to `microsoft/winget-pkgs` (or `wingetcreate`).

## Open points

- The macOS build is Apple Silicon only (`macos-latest`); the cask says `depends_on arch: :arm64`.
- File names were checked against the CI artifacts of run 44186563271 (`_x64-setup.exe`, `_x64_en-US.msi`, `_aarch64.dmg`); recheck on the first real release.
- Linux packages are attached to the release only; no apt/dnf repository.
