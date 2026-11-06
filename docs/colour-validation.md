# Colour validation - SoftProf 2.2.4

Date: 6 November 2026. Photoshop 27.11.0; 125 synthetic sRGB colours per case. Two installed printer profiles, three rendering intents and BPC on/off: 12 conversions, followed by three viewing conversions (36 comparisons). No user photos or ICC files are redistributed.

This is an independent **numerical profile-conversion comparison**, not a capture or validation of Photoshop's View > Proof Colors display pipeline. Photoshop converts the synthetic image into the printer profile and then into Display P3. SoftProf performs its own conversions using LittleCMS. Dither is off. The Photoshop colour engine/settings already configured on the test machine were retained; the tool does not select or establish an Adobe ACE engine configuration. The tool restores dialog handling and the previously active document, and closes only its own generated documents.

## Confirmed correction

For the HFA printer profile, relative colorimetric rendering without BPC, LittleCMS's default optimisation produced a maximum printer-colour difference of 10.717 Delta E76 against Photoshop. Disabling the extra optimisation reduced this to 0.433. Synthetic sRGB gray (32,32,32) previously became printer RGB (5,8,63); Photoshop gave (1,1,7). The corrected path matches this gray within one channel step. A profile-hash-pinned regression test preserves this independent reference.

NOOPTIMIZE disables the additional CMM optimisation, not the interpolation required by the ICC profile's own LUT. It does not guarantee agreement between different colour engines.

## Measured results

The table gives the maximum Delta E76 over all 125 patches. The viewing column takes the maximum over normalised black, simulated black ink and simulated paper plus ink. Both outputs are evaluated through the same absolute D50 Lab measurement path. Large errors can be concentrated in a few saturated or dark patches; see the JSON for means and channel differences.

| Profile | Intent | BPC | Printer max Delta E76 | Viewing max Delta E76 |
| --- | --- | --- | --- | --- |
| HFA_Eps3880_MK_GermEtching | Perceptual | Off | 1.967 | 6.366 |
| HFA_Eps3880_MK_GermEtching | Perceptual | On | 0.793 | 3.538 |
| HFA_Eps3880_MK_GermEtching | Relative | Off | 0.433 | 3.254 |
| HFA_Eps3880_MK_GermEtching | Relative | On | 2.222 | 5.656 |
| HFA_Eps3880_MK_GermEtching | Absolute | Off | 0.000 | 3.425 |
| HFA_Eps3880_MK_GermEtching | Absolute | On | 0.000 | 3.425 |
| ISO Coated v2 (ECI) | Perceptual | Off | 2.426 | 5.449 |
| ISO Coated v2 (ECI) | Perceptual | On | 0.415 | 1.062 |
| ISO Coated v2 (ECI) | Relative | Off | 0.371 | 0.793 |
| ISO Coated v2 (ECI) | Relative | On | 0.260 | 0.839 |
| ISO Coated v2 (ECI) | Absolute | Off | 0.261 | 0.779 |
| ISO Coated v2 (ECI) | Absolute | On | 0.261 | 0.779 |

Remaining differences are real; these results do not establish visual equivalence with Photoshop. Full resolution removes preview downsampling, but processing and export remain 8-bit. Display P3 can still clip colours. A calibrated-monitor/physical-print comparison and direct Photoshop Proof Colors comparison remain necessary for broader validation.

## Repeat the comparison

Requires macOS, installed Photoshop 2026, the source environment, and permission for local Photoshop automation. Only use a new output directory; the tool refuses to reuse an existing directory.

```sh
.venv/bin/python tools/validate_photoshop.py \
  --printer /path/to/RGB-printer.icc \
  --printer /path/to/CMYK-printer.icc \
  --output local-config/new-photoshop-validation
```

[Machine-readable results and ICC hashes](colour-validation-2.2.4.json). Full synthetic fixtures stay in the local output directory.

References: [Adobe proofing settings](https://helpx.adobe.com/uk/photoshop/using/proofing-colors.html), [Adobe profile conversion options](https://helpx.adobe.com/photoshop/desktop/adjust-color/color-profiles/change-color-profile-for-documents.html).

Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>. GPL-3.0-or-later.
