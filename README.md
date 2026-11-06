# SoftProf

A Python macOS application for comparing ICC colour-space conversions and simulating printer/paper output. Compare the original and a soft proof side by side, lock an A/B reference, and click an image to follow a colour through the source, working and printer profiles in CIELAB D50.

**Version:** 2.2.4
**Author:** Christer Törnkvist
**Contact:** [christer@borgasundsfotografiska.se](mailto:christer@borgasundsfotografiska.se)
**License:** [GNU GPL version 3 or later](LICENSE) (`GPL-3.0-or-later`). No warranty. See [license scope](LICENSE_SCOPE.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## Install

Download the installer from [GitHub Releases](https://github.com/chto0703009/SoftProf/releases/latest). The file is `SoftProf-2.2.4-macos.dmg` for **macOS 14 or later**. It contains two separately labelled apps, not one universal binary: **SoftProf - Apple Silicon.app** (ARM64) and **SoftProf - Intel.app** (x86_64).

1. Open the DMG and drag **only the app matching your Mac** to Applications: **Apple Silicon** for an Apple-chip Mac (M1/M2/M3 etc), or **Intel** for an Intel Mac.
2. Eject the disk image and launch the app from Applications.

| Your Mac | App to install | Execution |
| --- | --- | --- |
| Apple Silicon (M1, M2, M3 and later Apple chips) | SoftProf - Apple Silicon.app; ARM64 badge | Native ARM64, no Rosetta |
| Intel processor | SoftProf - Intel.app; INTEL badge | Native x86_64 on an Intel Mac |

Check **Apple menu > About This Mac** if you are unsure which processor you have. Choose one app; you do not need to install both. Rosetta was used to test the Intel build on the Apple Silicon development machine; it is not required to run the Intel app on an Intel Mac.

Open an image and select the printer/paper ICC profile.

Python and the required libraries are included. The installed app does not require this repository, Xcode or a separate Python installation. The package is ad hoc signed, but is not Developer ID signed or Apple-notarized. If macOS blocks the first launch, review the app in **System Settings > Privacy & Security > Open Anyway**.

The DMG also contains the full GPL text, author/contact information, both manuals and a source archive. Dependency notices are inside the app at `Contents/Resources/Notices`.

**GitHub repository:** [https://github.com/chto0703009/SoftProf](https://github.com/chto0703009/SoftProf)

## Documentation

- [English user guide (Markdown)](docs/softproof.en.md)
- [Svensk handbok (Markdown)](docs/softproof.sv.md)
- [English manual (PDF)](output/pdf/SoftProf-Manual-en.pdf)
- [Svensk handbok (PDF)](output/pdf/SoftProf-Manual-sv.pdf)

## Features

- Embedded source ICC profiles, or explicit source-profile selection for untagged images.
- Working spaces: sRGB, Adobe RGB (1998), Display P3, ProPhoto RGB via the macOS ROMM RGB profile, and custom ICC files.
- Printer/paper soft proof with relative colorimetric, absolute colorimetric or perceptual rendering, with optional black point compensation.
- Optional paper-white simulation, A/B reference lock and linked zoom/scroll.
- Click-to-sample gamut analysis in the a*/b* plane, with approximate colour backgrounds, Lab values and channel values for each stage.
- Full-resolution TIFF/PNG/JPEG export with the selected printer ICC file embedded byte for byte; original-file overwrite protection.
- Live Swedish/English UI, saved language preference, visible ARM/Intel/Rosetta runtime information and a Quit button at the bottom right.
- Author, contact and GPL information in the About menu; a menu item opens the full license.

## Colour handling and limits

The app uses Pillow/LittleCMS for ICC processing and PyObjC for AppKit/ColorSync display. Tagged Display P3 previews are adapted to the current monitor by macOS. Display P3 is an intermediate display space and can limit colours beyond its gamut.

This version supports one image frame and **8 bits per channel**. Previews retain full pixel dimensions, including at 100% zoom. Larger files take more memory and processing time. RGB PNG/TIFF files above 8 bits per channel are rejected before decoding; create a separate 8-bit copy first. Export uses the full image dimensions, still at 8 bits per channel. Export preserves ICC, DPI and supported transparency, not all source metadata. JPEG is lossy.

Gamut outlines are convex envelopes of sampled device values projected onto a plane. They are approximate, may overestimate concave gamut regions and do not provide exact in/out-of-gamut classification. CMYK sampling does not impose a separate total ink limit. Printed Lab positions are profile predictions, not measurements. A screen proof cannot establish that the physical print chain is colour unmanaged.

## Run from source

Use Python 3.13 on macOS, matching the architecture you want to run. The DMG supplies separate ARM64 and x86_64 apps. Each app is audited to contain only its own Mach-O architecture; an unrelated Homebrew LittleCMS library is excluded. The Apple Silicon app runs natively without Rosetta. Intel testing on the build machine uses Rosetta; a physical Intel Mac has not been tested.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/softproof_app.py
```

Alternatively, double-click `Starta SoftProf.command` after creating the environment. `tools/launch_softproof.py` creates a development app launcher that uses this environment. It is separate from the self-contained installer.

Core modules are `tools/icc_processing.py`, `tools/softproof_engine.py`, `tools/gamut_analysis.py`, `analysis/lcms_float.py` and `tools/runtime_architecture.py`. The GUI is `tools/softproof_app.py`; presentation strings are in `tools/softproof.en.json`. No Swift source or compiler is required.

[Independent Photoshop comparison and remaining limits](docs/colour-validation.md). Printer transforms disable LittleCMS optimisation to avoid additional dark-tone interpolation errors.

Colour regression checks compare sRGB-to-Lab against an independent mathematical reference and verify previews against reopened TIFF exports for installed RGB/CMYK printer profiles, all three intents, BPC on/off and paper white on/off. These are numerical checks; a calibrated-screen/physical-print comparison remains necessary for visual validation.

## Test

```sh
.venv/bin/python -m unittest discover -s tests -p 'test_softproof_*.py'
.venv/bin/python tools/softproof_app.py --startup-check
```

A GUI integration check is available with a supplied test image and printer profile:

```sh
INKPROF_SOFTPROOF_PREFERENCES_SUITE=se.inkprof.softproof.tests.manual \
.venv/bin/python tools/softproof_app.py \
  --smoke-test /path/to/test.tif /path/to/printer.icc /tmp/softproof-check.png \
  --clear-test-preferences
```

The check writes screenshots and a converted TIFF beside the requested screenshot path. Use a synthetic or disposable test image. The tests exercise conversion settings, alpha, profile persistence, original-file protection, exact-pixel sampling, gamut caching and architecture classification. The GUI check covers native windows, A/B, linked navigation, colour backgrounds, language switching and export.

## Rebuild the installer

Build each app with a Python environment matching its CPU. On Apple Silicon, the Intel environment can run through Rosetta if installed:

```sh
python3.13 -m venv local-config/build-arm/.venv
local-config/build-arm/.venv/bin/python -m pip install -r tools/requirements-softproof-build.txt
local-config/build-arm/.venv/bin/python tools/build_softproof_dmg.py --arch arm64 --app-only

arch -x86_64 python3.13 -m venv local-config/build-intel/.venv
arch -x86_64 local-config/build-intel/.venv/bin/python -m pip install -r tools/requirements-softproof-build.txt
arch -x86_64 local-config/build-intel/.venv/bin/python tools/build_softproof_dmg.py --arch x86_64 --app-only

local-config/build-arm/.venv/bin/python tools/build_softproof_dmg.py --combined-dmg
```

The build includes Python, required libraries, notices, architecture audit reports and corresponding application source. The audit fails if any Mach-O file has the wrong architecture. It writes the DMG and a SHA-256 file under `local-config/softproof-build/` and copies verified copies to Downloads. Personal photographs, measurements, project data, virtual environments and Git metadata are excluded from the source archive.

To regenerate manuals, install `tools/requirements-docs.txt` into a documentation environment and run `tools/render_manuals.py`. Outputs are stored under `output/pdf/`; verified copies are placed in Downloads. Font notices are retained in `licenses/fonts/`.

## License and contact

Copyright (c) 2026 **Christer Törnkvist** <christer@borgasundsfotografiska.se>.

This program is free software: you may redistribute and modify it under the GNU General Public License as published by the Free Software Foundation, either version 3 of the License or (at your option) any later version. It is distributed without any warranty. The unmodified full license is in [LICENSE](LICENSE). Third-party code and fonts retain their original terms.

---

GitHub: [chto0703009/SoftProf](https://github.com/chto0703009/SoftProf)
