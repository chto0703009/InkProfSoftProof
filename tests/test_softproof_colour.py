# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Colour regressions: analytic reference and exported-device round trips.

Printer integration cases use installed profiles, never redistribute them.
"""
import itertools
from pathlib import Path
import sys
import tempfile
import unittest
import numpy as np
from PIL import Image, ImageCms
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import softproof_engine as engine
from gamut_analysis import lab_values


class ColourTests(unittest.TestCase):
    def test_srgb_lab_against_independent_matrix_reference(self):
        # IEC sRGB transfer curve and Bradford-adapted D50 matrix. This path
        # deliberately uses no ICC transform to calculate expected Lab.
        rgb = np.array(list(itertools.product((0, 16, 64, 128, 192, 255), repeat=3)))
        v = rgb / 255
        linear = np.where(v <= .04045, v / 12.92, ((v + .055) / 1.055) ** 2.4)
        matrix = np.array([[.4360747, .3850649, .1430804],
                           [.2225045, .7168786, .0606169],
                           [.0139322, .0971045, .7141733]])
        xyz = (linear @ matrix.T) / np.array([.9642, 1., .8249])
        f = np.where(xyz > (6/29)**3, np.cbrt(xyz), xyz/(3*(6/29)**2)+4/29)
        expected = np.column_stack((116*f[:,1]-16, 500*(f[:,0]-f[:,1]), 200*(f[:,1]-f[:,2])))
        actual = np.array(lab_values(engine.load_profile('srgb'), rgb))
        self.assertLess(float(np.linalg.norm(actual-expected, axis=1).max()), .06)

    def test_preview_is_resized_after_colour_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            srgb = engine.load_profile('srgb')
            lab = ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
            image = Image.new('RGB', (2002, 2))
            image.putdata([(255,0,0), (0,255,0)] * 2002)
            source, printer, display = root/'source.tif', root/'lab.icc', root/'srgb.icc'
            image.save(source, icc_profile=srgb.tobytes())
            printer.write_bytes(lab.tobytes()); display.write_bytes(srgb.tobytes())
            request = dict(image=str(source), printer=str(printer), display=str(display), output=str(root/'preview'), intent=1, bpc=True)
            result = engine.run(request)
            full = engine.previews(image, srgb, srgb, lab, srgb, 1, True, False)[1]
            full.thumbnail((2000,2000), Image.Resampling.LANCZOS)
            with Image.open(root/'preview/proof.png') as actual:
                self.assertEqual(actual.tobytes(), full.tobytes())
                self.assertEqual(actual.width, result['previewWidth'])
            self.assertEqual(result['width'], 2002)

    def test_installed_printer_profiles_match_reopened_export(self):
        paths = [Path('/Library/ColorSync/Profiles/HFA_Eps3880_MK_GermEtching.icc'),
                 Path('/Library/ColorSync/Profiles/ISOcoated_v2_eci.icc')]
        paths = [p for p in paths if p.exists()]
        if not paths:
            self.skipTest('Install RGB/CMYK printer profiles for integration validation')
        srgb = engine.load_profile('srgb')
        lab = ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
        image = Image.new('RGB', (125, 1))
        image.putdata(list(itertools.product((0, 32, 128, 224, 255), repeat=3)))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.tif'; output = root/'export.tif'
            image.save(source, icc_profile=srgb.tobytes())
            image, srgb, _ = engine.load_image(source)
            working_path = root/'lab.icc'; working_path.write_bytes(lab.tobytes())
            for path, working, intent, bpc in itertools.product(paths, (None, working_path), (0,1,3), (False,True)):
                with self.subTest(printer=path.name, working=str(working), intent=intent, bpc=bpc):
                    engine.run(dict(action='save', image=str(source), destination=str(output), printer=str(path), working=str(working) if working else None, intent=intent, bpc=bpc))
                    printed, printer, _ = engine.load_image(output)
                    wp = engine.load_profile(working) if working else srgb
                    for paper in (False,True):
                        _, proof = engine.previews(image, srgb, wp, printer, srgb, intent, bpc, paper)
                        # Independently reopen the actual TIFF and proof its
                        # tagged device pixels. No BPC on this viewing leg.
                        reference = ImageCms.profileToProfile(printed, printer, srgb, renderingIntent=3 if paper else 1, outputMode='RGB', flags=0)
                        self.assertEqual(proof.tobytes(), reference.tobytes())
            # A printer's nonzero black must survive the screen conversion.
            printer = engine.load_profile(paths[0])
            _, proof = engine.previews(Image.new('RGB',(1,1)), srgb, srgb, printer, srgb, 1, True, False)
            self.assertGreater(max(proof.getpixel((0,0))), 10)

if __name__ == '__main__':
    unittest.main()
