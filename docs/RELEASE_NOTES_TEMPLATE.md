# moonpark vX.Y.Z

Landing-site × time evaluator for the lunar south pole. Desktop app with the engine bundled: nothing else to install or start.

## Download

| System | File | Notes |
|--------|------|-------|
| Windows 10/11 (64-bit) | `moonpark_X.Y.Z_x64-setup.exe` or `moonpark_X.Y.Z_x64_en-US.msi` | Unsigned, see below |
| macOS (Apple Silicon) | `moonpark_X.Y.Z_aarch64.dmg` | Unsigned, see below. Intel Macs are not built yet |
| Linux | `moonpark_X.Y.Z_amd64.AppImage`, `.deb` or `.rpm` | |

Or from a package manager:

```bash
winget install Pedrojonfg.Moonpark       # Windows (once accepted)
brew install --cask Pedrojonfg/moonpark/moonpark   # macOS
```

## First launch

The app is **not code-signed** (a certificate costs money this project does not have). Your system will warn you. The warning is about the missing signature, not about anything the app does; the source and the build workflow are public.

**Windows.** SmartScreen shows "Windows protected your PC". Click *More info*, then *Run anyway*.

**macOS.** The first time, macOS may say the app "is damaged" or "cannot be opened". Either:
- right-click the app in *Applications*, choose *Open*, then *Open* again; or
- in a terminal: `xattr -cr /Applications/moonpark.app`

Installing with the Homebrew command above removes the flag for you.

**Linux.**
- AppImage: `chmod +x moonpark_*.AppImage && ./moonpark_*.AppImage`
- Debian/Ubuntu: `sudo apt install ./moonpark_*_amd64.deb`
- Fedora: `sudo dnf install ./moonpark-*.rpm`

## First analysis downloads data

The first real analysis downloads the data it needs (kernels, terrain masks, and hazard rasters if enabled) from `masks.pedrojon.com`. The planner shows which file is downloading. It can take a few minutes and up to about 0.7 GB with hazards on. It is stored on your machine and not downloaded again; after that the app works offline.

To try the interface without downloading anything, tick **Mock data (demo)** in *New analysis*. Mock results are labelled and are not real analysis.

## The 3D view

By default the first-person view builds **our own LOLA relief** (procedural surface, no imagery) from the data store — **no Cesium ion token required**. Ion is optional: add a free [token](https://cesium.com/ion/tokens), add [Cesium Moon Terrain](https://ion.cesium.com/assetdepot/2684829) to your assets, and choose *Use Cesium ion* for the textured higher-resolution backdrop (also the automatic fallback when a site has no relief yet). Without own relief and without a token you get the 2D horizon panorama.

## Known limitations

- Battery, dust and noise parameters marked provisional in the README are not tuned yet.
- Windows and macOS builds are produced by CI and have not been run by the author on real machines. Please report problems.
