# InkProf Soft Proof

A Python macOS application for comparing ICC colour-space conversions and simulating printer/paper output. Compare the original and a soft proof side by side, lock an A/B reference, and click an image to follow a colour through the source, working and printer profiles in CIELAB D50.

**Version:** 2.1.2
**Author:** Christer Törnkvist
**Contact:** [christer@borgasundsfotografiska.se](mailto:christer@borgasundsfotografiska.se)
**License:** [GNU GPL version 3 or later](LICENSE) (`GPL-3.0-or-later`). No warranty. See [license scope](LICENSE_SCOPE.md) and [third-party notices](THIRD_PARTY_NOTICES.md).

## Install

The standalone installer is `InkProfSoftProof-2.1.2-arm64.dmg` for **Apple Silicon, macOS 14 or later**.

1. Open the DMG and drag **InkProf Soft Proof.app** to **Applications**.
2. Eject the disk image and launch the app from Applications.
3. Open an image and select the printer/paper ICC profile.

Python and the required libraries are included. The installed app does not require this repository, Xcode or a separate Python installation. The package is ad hoc signed, but is not Developer ID signed or Apple-notarized. If macOS blocks the first launch, review the app in **System Settings > Privacy & Security > Open Anyway**.

The DMG also contains the full GPL text, author/contact information, both manuals and a source archive. Dependency notices are inside the app at `Contents/Resources/Notices`.

## Documentation

- [English user guide (Markdown)](docs/softproof.en.md)
- [Svensk handbok (Markdown)](docs/softproof.sv.md)
- [English manual (PDF)](output/pdf/InkProfSoftProof-Manual-en.pdf)
- [Svensk handbok (PDF)](output/pdf/InkProfSoftProof-Manual-sv.pdf)

## Features

- Embedded source ICC profiles, or explicit source-profile selection for untagged images.
- Working spaces: sRGB, Adobe RGB (1998), Display P3, ProPhoto RGB via the macOS ROMM RGB profile, and custom ICC files.
- Printer/paper soft proof with relative colorimetric, absolute colorimetric or perceptual rendering, with optional black point compensation.
- Optional paper-white simulation, A/B reference lock and linked zoom/scroll.
- Click-to-sample gamut analysis in a*/b*, a*/L* and b*/L* projections, with approximate colour backgrounds, Lab values and channel values for each stage.
- Full-resolution TIFF/PNG/JPEG export with the selected printer ICC file embedded byte for byte; original-file overwrite protection.
- Live Swedish/English UI, saved language preference, visible ARM/Intel/Rosetta runtime information and a Quit button at the bottom right.
- Author, contact and GPL information in the About menu; a menu item opens the full license.

## Colour handling and limits

The app uses Pillow/LittleCMS for ICC processing and PyObjC for AppKit/ColorSync display. Tagged Display P3 previews are adapted to the current monitor by macOS. Display P3 is an intermediate display space and can limit colours beyond its gamut.

This version supports one image frame and **8 bits per channel**. Previews are reduced to at most 2,000 pixels on the long edge. Export uses the full image dimensions, still at 8 bits per channel. Export preserves ICC, DPI and supported transparency, not all source metadata. JPEG is lossy.

Gamut outlines are convex envelopes of sampled device values projected onto a plane. They are approximate, may overestimate concave gamut regions and do not provide exact in/out-of-gamut classification. CMYK sampling does not impose a separate total ink limit. Printed Lab positions are profile predictions, not measurements. A screen proof cannot establish that the physical print chain is colour unmanaged.

## Run from source

Use Python 3.13 on macOS. The supplied standalone DMG targets ARM64; architecture detection also distinguishes native Intel and Rosetta, without implying that the ARM64 installer can run on Intel hardware.

```sh
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python tools/softproof_app.py
```

Alternatively, double-click `Starta Soft proof.command` after creating the environment. `tools/launch_softproof.py` creates a development app launcher that uses this environment. It is separate from the self-contained installer.

Core modules are `tools/icc_processing.py`, `tools/softproof_engine.py`, `tools/gamut_analysis.py`, `analysis/lcms_float.py` and `tools/runtime_architecture.py`. The GUI is `tools/softproof_app.py`; presentation strings are in `tools/softproof.en.json`. No Swift source or compiler is required.

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

```sh
python3.13 -m venv local-config/softproof-build/.venv
local-config/softproof-build/.venv/bin/python -m pip install \
  -r tools/requirements-softproof-build.txt
local-config/softproof-build/.venv/bin/python tools/build_softproof_dmg.py
```

The build includes Python, required libraries, notices and corresponding application source. It writes the DMG and a SHA-256 file under `local-config/softproof-build/` and copies verified copies to Downloads. Personal photographs, measurements, project data, virtual environments and Git metadata are excluded from the source archive.

To regenerate manuals, install `tools/requirements-docs.txt` into a documentation environment and run `tools/render_manuals.py`. Outputs are stored under `output/pdf/`; verified copies are placed in Downloads. Font notices are retained in `licenses/fonts/`.

## License and contact

Copyright (c) 2026 **Christer Törnkvist** <christer@borgasundsfotografiska.se>.

This program is free software: you may redistribute and modify it under the GNU General Public License as published by the Free Software Foundation, either version 3 of the License or (at your option) any later version. It is distributed without any warranty. The unmodified full license is in [LICENSE](LICENSE). Third-party code and fonts retain their original terms.
