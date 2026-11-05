# InkProf Soft Proof

User guide - version 2.1.1 - 5 November 2026

Christer Törnkvist - christer@borgasundsfotografiska.se
GNU GPL version 3 or later (GPL-3.0-or-later).

## 1. Install and get started

InkProf Soft Proof compares an image with a prediction of its printed appearance. It helps you explore the consequences of a working colour space, printer/paper ICC profile, rendering intent and black point compensation before exporting a converted image.

### Install the app

Open `InkProfSoftProof-2.1.1-arm64.dmg`, drag **InkProf Soft Proof.app** to **Applications**, eject the disk image and launch the app from Applications. The standalone package targets **Apple Silicon and macOS 14 or later**. Python and the required libraries are included; the development project is not needed.

The package is ad hoc signed, but not Developer ID signed or Apple-notarized. If macOS blocks the first launch, review it in **System Settings > Privacy & Security > Open Anyway**. The DMG includes both manuals, the GPL license and application source.

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

### Screen colour management

Previews are ICC-tagged Display P3 images shown through macOS AppKit/ColorSync. The operating system adapts them to the monitor displaying the window, including when the window changes screens. Do not select the monitor profile as a working or printer profile. Display P3 itself can limit colours beyond that intermediate space.

## 3. Compare and select a colour

### Side-by-side comparison

The left view starts as the original interpreted with its source profile. The right view follows the current working-space and printer settings. Without a printer profile, the right view shows only the working-space conversion.

Choose **Lock simulation as reference** to keep result A on the left. Change profiles, rendering intent or compensation to create result B on the right. The reference caption preserves the settings used for A. **Show original on the left** returns to the original comparison.

### Zoom and scroll

Both views share zoom and scrolling. **Fit** shows the whole image; 25%, 50% and 100% use the original dimensions as their size reference. Preview processing is limited to 2,000 pixels on the long edge, so 100% can enlarge the reduced preview for larger originals. It is not full-resolution pixel inspection.

### Click-to-sample

Click either image to open the gamut window and follow the corresponding original pixel. A crosshair marks the location in both views. The sample is read from the original file after EXIF orientation, independently of preview reduction and zoom.

Clicking a locked reference still follows that original pixel through the **current** profile settings. It does not sample the reference's old conversion. Changing settings updates the same selected pixel. Selecting a new image clears the reference and sample.

### Read the stage values

The gamut window reports source, working-space and predicted printer values. RGB or CMYK channel numbers may change while the Lab position stays almost unchanged: a colour-preserving conversion aims to keep the colour, not the same numbers. A movement indicates a predicted colour change, for example from gamut mapping or 8-bit quantisation.

## 4. Read the gamut diagram

All profiles are compared in **CIELAB D50**. Choose a*/b* for a top view, a*/L* for a front view, or b*/L* for a side view. Axis units use a common scale, expanding when necessary without shrinking as settings change.

<!-- gamut -->

### Contours, points and arrows

The contours show the source, working and printer profiles. Toggle them separately to reduce clutter. Numbered points and arrows follow **original > working space > predicted print**. Grey rings show the previous settings for the same pixel.

The numerical rows show L*, a*, b*, device-channel values and **ΔE76 from the original**. Lab is evaluated through LittleCMS with floating-point output and fixed absolute D50 colourimetry. Device-channel conversions follow the same 8-bit pipeline as export. The printer point is the profile's prediction, not a measured print. The screen profile and paper-white preview toggle are not part of these analysis coordinates.

### Approximate colour background

**Colour-tinted background** supplies a hue guide; **Strength** adjusts its visibility. In a*/b*, it uses the original sample's L* or 65 before selection. The side views hold b*=0 or a*=0. These are coloured slices behind projected contours, not a measurement of all colours in that projection. Display clipping and tinting make the background approximate.

### Do not use outlines as an exact gamut test

Contours are convex outer envelopes of sampled ICC device values, projected onto a plane. They merge the third dimension and may overestimate concave regions. Sampling uses 17 levels per RGB/Lab channel and 9 per CMYK channel, without a separate CMYK total-ink limit. A point inside a contour does not prove that the colour is printable at its L*.

## 5. Export and print

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

The app supports one image frame and **8 bits per channel**. Export keeps full pixel dimensions, the ICC profile, DPI and supported alpha. It does not preserve all EXIF/XMP or other metadata. JPEG is lossy. Paper-white simulation is not baked into the export. The preview's 2,000-pixel limit does not reduce export dimensions.

A successful export or small predicted ΔE is not evidence of measured print accuracy. Assess important work with a correctly prepared physical test print.

## 6. Language, architecture and license

### Language and exit

Select **Svenska** or **English** at **Språk / Language**. Both windows, menus, status messages and application errors update immediately. Profile choices, the selected pixel and locked reference are preserved. The choice is restored on the next launch. Profile names and filenames are not translated; macOS-owned buttons and system errors may follow the system language.

**Quit** is at the bottom right of the main window. You can also use the app menu or Command-Q.

### ARM, Intel and Rosetta

The bottom status area distinguishes computer hardware, the Python process architecture and native or Rosetta execution. Rosetta is queried inside the Python process. Unavailable information is reported as **Unknown**, rather than guessed. Native ARM, native Intel and Rosetta classifications are tested; the supplied installer itself is ARM64 and has been verified on Apple Silicon.

### GPL license and contact

Copyright (c) 2026 **Christer Törnkvist**.
Email: **christer@borgasundsfotografiska.se**.

The application and documentation are free software under the **GNU General Public License, version 3 or any later version** (GPL-3.0-or-later). They are provided without warranty. The full unmodified license is in **LICENSE**. Third-party code, system resources and fonts retain their own terms; see **LICENSE_SCOPE.md** and **THIRD_PARTY_NOTICES.md**.

The app menu offers **About InkProf Soft Proof** with author, contact and license information, and **View the GPL license** opens the full text. The DMG includes application source, build tools and both manuals. The English README explains source installation, tests and rebuilding the DMG. No personal photographs, measurements or local virtual environments are included in the Git repository or source archive.
