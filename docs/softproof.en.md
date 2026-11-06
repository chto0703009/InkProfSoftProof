# SoftProf

User guide - version 2.4.1 - 6 November 2026

Christer Törnkvist - christer@borgasundsfotografiska.se
GNU GPL version 3 or later (GPL-3.0-or-later).

## 1. Install and get started

SoftProf compares an image with a prediction of its printed appearance. It helps you explore the consequences of a working colour space, printer/paper ICC profile, rendering intent and black point compensation before exporting a converted image.

### Install the app

Open `SoftProf-2.4.1-macos.dmg`, choose **Apple Silicon** or **Intel** to match your Mac and drag that app to **Applications**, eject the disk image and launch the app from Applications. The DMG contains two labelled apps: **Apple Silicon requires macOS 14+; Intel requires macOS 13 Ventura+**. Apple Silicon is ARM64; Intel is x86_64. All bundled Intel binaries are checked against the Ventura deployment target. Physical Ventura hardware has not been tested here. Install only the matching app. Python and the required libraries are included; the development project is not needed.

The package is ad hoc signed, but not Developer ID signed or Apple-notarized. If macOS blocks the first launch, review it in **System Settings > Privacy & Security > Open Anyway**. The DMG includes both manuals, the GPL license and application source.

### Choose the app for your Mac

| Computer | App and badge |
| --- | --- |
| Apple Silicon, such as M1, M2 or M3 | SoftProf - Apple Silicon.app, ARM64 badge |
| Intel processor | SoftProf - Intel.app, INTEL badge |

Check **Apple menu > About This Mac** if unsure. Install one app. ARM64 runs natively without Rosetta on Apple Silicon; the Intel app runs natively on an Intel Mac. Rosetta is used only in our Intel-build test on Apple Silicon.

### Start with a known image

Choose **Open image**, then select the working colour space and printer/paper ICC profile. The original appears on the left and the current simulation on the right. An untagged image needs an explicitly chosen source profile before its colours can be interpreted.

<!-- pipeline -->

The conversion path is: **source profile > working colour space > printer/paper profile**. A separate display conversion prepares the proof for the screen; macOS ColorSync adapts the tagged preview to the current monitor.

### Keep the physical setup consistent

Use the ICC profile for the actual printer, paper, ink and driver settings. The monitor, its calibration and the light used to view a print affect the comparison. Soft proofing is a profile-based estimate, not a measurement or a guarantee of a matching print.

## 2. Profiles and rendering

### Source profile and working colour space

An embedded ICC profile is always used as the source. For an image without a profile, select the profile that actually describes its stored values. Assigning that interpretation does not change the original file. Choosing the wrong source profile changes the meaning of every colour.

The working-space menu offers sRGB, Adobe RGB (1998), Display P3, ProPhoto RGB and a custom ICC file. ProPhoto RGB uses the macOS ROMM RGB system profile. **Keep the image colour space** avoids an unnecessary working-space round trip. The chosen rendering intent and black point compensation apply to conversions into the working space and from it to the printer profile.

| Rendering intent | Practical interpretation |
| --- | --- |
| Relative colorimetric | Adapts white to the destination and maps colours outside its gamut. |
| Absolute colorimetric | Preserves absolute colourimetry, including the profile's white-point relationship. |
| Perceptual | Uses the profile's perceptual mapping, when provided, to preserve visual relationships. |

Different intents can produce the same result when the profile does not provide distinct mappings.

### Black point compensation and paper white

**Black point compensation** adjusts the mapping of dark tones between profiles. Its visible effect depends on the profiles and rendering intent.

**Simulate paper white** is a separate screen-proof setting. It selects absolute colorimetric proof-to-display rendering; the selected printer conversion intent remains a separate stage. This setting affects the preview, not the saved printer pixels.

**Simulate black ink** preserves the printer profile’s predicted black. Turn it off, with paper white off, to map black to screen black. Paper-white simulation also enables black-ink simulation. These viewing choices do not change export. The preview uses the same 8- or 16-bit printer values as export; LittleCMS optimisation is disabled to avoid extra interpolation errors. JPEG export can introduce additional changes.

### Screen colour management

Previews are ICC-tagged Display P3 images shown through macOS AppKit/ColorSync. The operating system adapts them to the monitor displaying the window, including when the window changes screens. Do not select the monitor profile as a working or printer profile. Display P3 itself can limit colours beyond that intermediate space.

## 3. Compare and select a colour

### Side-by-side comparison

The left view starts as the original interpreted with its source profile. The right view follows the current working-space and printer settings. Without a printer profile, the right view shows only the working-space conversion.

Choose **Lock simulation as reference** to keep result A on the left. Change profiles, rendering intent or compensation to create result B on the right. The reference caption preserves the settings used for A. **Show original on the left** returns to the original comparison.

### Zoom and scroll

Both views share zoom and scrolling. **Fit** shows the whole image; 25%, 50% and 100% use the original dimensions. The preview retains all pixels, so 100% no longer enlarges a reduced preview. At 100%, one image pixel maps to one backing display pixel, accounting for Retina scaling. Large images require more memory and take longer to process.

### Click-to-sample

Click either image to open the gamut window and follow the corresponding original pixel. A crosshair marks the location in both views. The sample is read from the original file after EXIF orientation, independently of preview reduction and zoom.

Clicking a locked reference still follows that original pixel through the **current** profile settings. It does not sample the reference's old conversion. Changing settings updates the same selected pixel. Selecting a new image clears the reference and sample.

### Read the stage values

The gamut window reports source, working-space and predicted printer values. RGB or CMYK channel numbers may change while the Lab position stays almost unchanged: a colour-preserving conversion aims to keep the colour, not the same numbers. A movement indicates a predicted colour change, for example from gamut mapping or quantisation.

## 4. Read the gamut diagram

All profiles are compared in **CIELAB D50**. The default 2D diagram shows the a*/b* plane from above. Axis units use a common scale, expanding when necessary without shrinking as settings change.

<!-- gamut -->

### Contours, points and arrows

The contours show the source, working and printer profiles. Toggle them separately to reduce clutter. Numbered points and arrows follow **original > working space > predicted print**. Grey rings show the previous settings for the same pixel.

The numerical rows show L*, a*, b*, device-channel values and **ΔE76 from the original**. Lab is evaluated through LittleCMS with floating-point output and fixed absolute D50 colourimetry. Device-channel conversions follow the same 8- or 16-bit pipeline as export. The printer point is the profile's prediction, not a measured print. The screen profile and paper-white preview toggle are not part of these analysis coordinates.

### Approximate colour background

**Colour-tinted background** supplies a hue guide; **Strength** adjusts its visibility. Turn off **Follow sample L*** to choose background lightness from **0 to 100** with the slider or numeric field (press Enter). L* 0 is black and 100 is white. Turn it on to follow the original sample's L*, or 65 before selection. This changes only the approximate background, not samples, contours or export. The background is a coloured slice at the chosen L* behind the projected contours, not a measurement of all colours in that projection. Display clipping and tinting make the background approximate.

### Do not use outlines as an exact gamut test

Contours are convex outer envelopes of sampled ICC device values, projected onto a plane. They merge the third dimension and may overestimate concave regions. Sampling uses 17 levels per RGB/Lab channel and 9 per CMYK channel, without a separate CMYK total-ink limit. A point inside a contour does not prove that the colour is printable at its L*.

## 5. 3D colour space

Choose **Show 3D colour space**; **Show 2D** restores the existing diagram. Choose **Original**, **Working space** or **Print** in the 3D view menu. Drag the plot to rotate, scroll to zoom, or choose **Reset 3D view**. L* increases upwards towards lighter colours, a* runs from green (negative) to red (positive), and b* from blue (negative) to yellow (positive). Follow the labelled axes after rotating the view. The selected image pixel is marked with a white ring in the chosen stage. The L* background controls apply only to 2D.

Enable **Show movement**, then change a working space, printer profile, rendering intent or BPC in the main window. The same representatives animate from the previous positions to the new ones; bright yellow arrows remain for comparison. Arrowheads point to the new result. The text below the plot explains this direction and identifies the before/after working spaces and displayed stages, including when you change colour space. Changing the displayed stage also shows its movement. Disable the option for a static view. Colour-preserving conversions may barely move; paper-white and ink viewing toggles do not alter absolute Lab positions.

The 3D view shows up to 1,024 frequent groups from at most 65,536 deterministic stratified pixel samples. Nearby source channel values share a group; an actual source pixel represents each group. The smaller points improve visibility in dense regions; point size still increases with approximate sampled frequency; fully transparent pixels are omitted and partial alpha weights frequency. Rare colours may be omitted. The points are an image distribution, not a solid profile-gamut shell. Their Display P3 screen colours are approximate. Original photographs are unchanged.

<!-- cloud -->

## 6. Export and print

Choose **Convert and save** after selecting an image and printer/paper profile. The app processes the full image via the selected working space and printer profile, then embeds the selected printer ICC file **byte for byte**. The source image cannot be overwritten.

| Format | Supported output channels |
| --- | --- |
| TIFF | RGB, RGBA, CMYK, greyscale, greyscale with alpha, Lab |
| PNG | RGB, RGBA, greyscale, greyscale with alpha |
| JPEG | RGB, CMYK, greyscale; no alpha; lossy compression |

An incompatible channel/format combination is rejected rather than silently changed. Transparency can be retained through RGB or greyscale processing; CMYK/Lab conversion with alpha is rejected. Transparent colour samples are analysed before compositing with a background, and their alpha is shown separately.

### Print the converted values once

The exported image is already converted to the printer profile. Print these values with further application, operating-system and driver colour conversion disabled. Use the same printer, paper, media and quality settings as the ICC profile. The app exports files; it does not control or verify the printer driver or physical print chain.

### Version limits

The app supports one image frame and **8 or unsigned 16 bits per channel**. For 16-bit images, RGB/RGBA and grayscale/alpha use TIFF or PNG; CMYK uses TIFF. TIFF supports uncompressed, LZW, Deflate/ZIP and PackBits data, separate planes and orientation. ICC conversion, selected pixels, 3D positions and TIFF/PNG export retain 16-bit precision. Values range from 0 to 65,535 instead of 0 to 255. JPEG is 8-bit only and cannot be chosen for 16-bit sources. File-based 16-bit Lab and 32-bit/floating-point images are unsupported; a Lab working profile is still supported. Export retains pixel dimensions, ICC, DPI and supported alpha, not all EXIF/XMP. Paper and ink simulation are not baked into export.

A successful export or small predicted ΔE is not evidence of measured print accuracy. Assess important work with a correctly prepared physical test print.

A synthetic numerical comparison with Photoshop 27.11 found and corrected a dark-tone optimisation error. Remaining differences are documented in the GitHub colour-validation report. This is not a verification of Photoshop’s on-screen Proof Colors or physical print accuracy.

## 7. Language, architecture and license

### Language and exit

Select **Svenska** or **English** at **Språk / Language**. Both windows, menus, status messages and application errors update immediately. Profile choices, the selected pixel and locked reference are preserved. The choice is restored on the next launch. Profile names and filenames are not translated; macOS-owned buttons and system errors may follow the system language.

**Quit** is at the bottom right of the main window. You can also use the app menu or Command-Q.

### ARM, Intel and Rosetta

The bottom status area distinguishes computer hardware, the Python process architecture and native or Rosetta execution. Rosetta is queried inside the Python process. Unavailable information is reported as **Unknown**, rather than guessed. Native ARM, native Intel and Rosetta classifications are tested; the DMG contains separate ARM64 and x86_64 apps with strict binary audits. ARM64 is tested natively; Intel is tested via Rosetta on Apple Silicon, not on a physical Intel Mac.

### GPL license and contact

Copyright (c) 2026 **Christer Törnkvist**.
Email: **christer@borgasundsfotografiska.se**.

The application and documentation are free software under the **GNU General Public License, version 3 or any later version** (GPL-3.0-or-later). They are provided without warranty. The full unmodified license is in **LICENSE**. Third-party code, system resources and fonts retain their own terms; see **LICENSE_SCOPE.md** and **THIRD_PARTY_NOTICES.md**.

The app menu offers **About SoftProf** with author, contact and license information, and **View the GPL license** opens the full text. The DMG includes application source, build tools and both manuals. The English README explains source installation, tests and rebuilding the DMG. No personal photographs, measurements or local virtual environments are included in the Git repository or source archive.

---

GitHub: [chto0703009/SoftProf](https://github.com/chto0703009/SoftProf)
