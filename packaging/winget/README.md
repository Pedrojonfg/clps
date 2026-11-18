# winget

`Pedrojonfg.LunarEval.*.yaml` are templates for a manifest in
[microsoft/winget-pkgs](https://github.com/microsoft/winget-pkgs). After publishing a release:

1. Replace `X.Y.Z`, the installer URL and `InstallerSha256`
   (`certutil -hashfile <file> SHA256` on Windows, or `sha256sum`).
2. `License` is MIT (see LICENSE).
3. Validate: `winget validate packaging/winget` (Windows).
4. Open a PR to `microsoft/winget-pkgs` under `manifests/p/Pedrojonfg/LunarEval/X.Y.Z/`
   (or use `wingetcreate update Pedrojonfg.LunarEval --urls <url> --version X.Y.Z --submit`).
   Their bot validates the installer; an unsigned one may need a manual review.
