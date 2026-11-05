# Third-party notices

InkProf Soft Proof is copyright (c) 2026 Christer Törnkvist,
christer@borgasundsfotografiska.se, and licensed under GPL-3.0-or-later.
The full license is in LICENSE. Dependencies keep their own licenses.

## Runtime dependencies

| Component | Version used | License / purpose |
| --- | --- | --- |
| Python | 3.13.6 | PSF license and bundled notices; application runtime |
| Pillow | 12.3.0 | MIT-CMU and bundled notices; image I/O and ICC transforms |
| LittleCMS | as bundled with Pillow | MIT; ICC conversion and float Lab evaluation |
| NumPy | 2.3.2 | BSD and bundled notices; numerical gamut analysis |
| PyObjC core, Cocoa and Quartz | 13.0 | MIT; Python bridge to macOS AppKit/ColorSync |
| PyInstaller | 6.22.3 | GPL with bootloader exception; standalone packaging |

Complete notices for the actual installed build dependencies are copied into
the app at `Contents/Resources/Notices`, together with a version inventory.
PyObjC notices retained in the source tree are in licenses/softproof-python/;
that directory records their provenance and SHA-256 hashes.

## Documentation tools and fonts

ReportLab 5.0.1 and pypdf 6.18.1 are optional documentation dependencies.
The manuals use DejaVu Sans (regular and bold), with their upstream font
licenses preserved in licenses/fonts/. Font files are not relicensed under GPL.

## System resources and user material

AppKit, ColorSync and system ICC profiles are macOS components, not bundled
third-party binaries. ProPhoto RGB uses the macOS ROMM RGB profile. User images
and user-selected profiles keep their original ownership and are not included
in the repository or installer. No Argyll executables or reference profiles
are distributed with this standalone app.

## Installer source

Each DMG includes a source archive of the GPL application and its build tools,
README, manuals and license declarations. Python and other bundled dependencies
retain the licenses included in the app. The development launcher uses a local
Python environment; the standalone DMG additionally bundles the runtime.
