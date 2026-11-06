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

    def test_preview_is_resized_before_colour_conversion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            srgb = engine.load_profile('srgb')
            lab = ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
            image = Image.new('RGB', (2002, 2))
            image.putdata([(255,0,0), (0,255,0)] * 2002)
            source, printer, display = root/'source.tif', root/'lab.icc', root/'srgb.icc'
            image.save(source, icc_profile=srgb.tobytes())
            printer.write_bytes(lab.tobytes()); display.write_bytes(srgb.tobytes())
            request = dict(image=str(source), printer=str(printer), display=str(display), output=str(root/'preview'), previewLimit=2000, intent=1, bpc=True)
            result = engine.run(request)
            image, srgb, _ = engine.load_image(str(source))
            image.thumbnail((2000,2000), Image.Resampling.LANCZOS)
            full = engine.previews(image, srgb, srgb, engine.load_profile(str(printer)), engine.load_profile(str(display)), 1, True, False)[1]
            with Image.open(root/'preview/proof.png') as actual:
                self.assertEqual(actual.tobytes(), full.tobytes())
                self.assertEqual(actual.width, result['previewWidth'])
            self.assertEqual(result['width'], 2002)

    def test_16bit_rgb_is_loaded_without_precision_loss(self):
        import struct
        import zlib
        def chunk(kind, data):
            return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind+data) & 0xffffffff)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            png = root/'rgb16.png'
            png.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 1,1,16,2,0,0,0)) + chunk(b'IDAT', zlib.compress(b'\0'+struct.pack('>3H', 4660,22136,39612))) + chunk(b'IEND', b''))
            # A minimal uncompressed RGB16 TIFF, independent of Pillow's writer.
            entries = [(256,4,1,1),(257,4,1,1),(258,3,3,134),
                       (259,3,1,1),(262,3,1,2),(273,4,1,140),
                       (277,3,1,3),(278,4,1,1),(279,4,1,6),(284,3,1,1)]
            tiff = root/'rgb16.tif'
            tiff.write_bytes(b'II'+struct.pack('<HIH',42,8,len(entries))+b''.join(struct.pack('<HHII',*entry) for entry in entries)+struct.pack('<I',0)+struct.pack('<3H',16,16,16)+struct.pack('<3H',4660,22136,39612))
            for path in (png,tiff):
                with self.subTest(format=path.suffix):
                    before = path.read_bytes()
                    loaded,_,_=engine.load_image(path,'srgb')
                    self.assertEqual(loaded.bits,16)
                    self.assertEqual(loaded.getpixel((0,0)),(4660,22136,39612))
                    self.assertEqual(path.read_bytes(), before)

    def test_default_preview_retains_full_pixel_dimensions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); source = root/'source.png'; profile = root/'srgb.icc'
            srgb = engine.load_profile('srgb'); profile.write_bytes(srgb.tobytes())
            image = Image.new('RGB', (2401,3)); image.putpixel((2200,1),(211,14,82))
            image.save(source, icc_profile=srgb.tobytes())
            result = engine.run(dict(image=str(source), display=str(profile), output=str(root/'out')))
            for name in ('original','proof'):
                with Image.open(root/'out'/f'{name}.png') as preview:
                    self.assertEqual(preview.size, image.size)
                    self.assertEqual(preview.getpixel((2200,1)), (211,14,82))
            self.assertEqual(result['previewWidth'], 2401)

    def test_dark_gray_against_photoshop_reference(self):
        # Photoshop 27.11 conversion of synthetic sRGB (32,32,32), relative
        # colorimetric, BPC/dither off. Independent reference, not a second
        # invocation of the implementation. Pin the installed ICC fixture.
        import hashlib
        path = Path('/Library/ColorSync/Profiles/HFA_Eps3880_MK_GermEtching.icc')
        if not path.exists(): self.skipTest('Requires installed printer fixture')
        expected_hash = '9090f322b5f228cd239a50cd95f2fd3b0cceae52e666aa4875d0ed693ab93bd2'
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            self.skipTest('Installed ICC differs from the reference fixture')
        source = engine.load_profile('srgb'); printer = engine.load_profile(path)
        actual = engine.process(Image.new('RGB',(1,1),(32,32,32)),source,printer,'RGB',1,False).getpixel((0,0))
        self.assertTrue(all(abs(a-b)<=1 for a,b in zip(actual,(1,1,7))), actual)

    def test_black_ink_toggle_and_paper_dependency(self):
        path = Path('/Library/ColorSync/Profiles/HFA_Eps3880_MK_GermEtching.icc')
        if not path.exists(): self.skipTest('Requires installed RGB printer profile')
        s = engine.load_profile('srgb'); p = engine.load_profile(path)
        image = Image.new('RGB',(1,1))
        simulated = engine.previews(image,s,s,p,s,1,True,False,True)[1]
        normalised = engine.previews(image,s,s,p,s,1,True,False,False)[1]
        self.assertGreater(sum(simulated.getpixel((0,0))), sum(normalised.getpixel((0,0))))
        a = engine.previews(image,s,s,p,s,1,True,True,True)[1]
        b = engine.previews(image,s,s,p,s,1,True,True,False)[1]
        self.assertEqual(a.tobytes(), b.tobytes())

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
                        reference = ImageCms.profileToProfile(printed, printer, srgb, renderingIntent=3 if paper else 1, outputMode='RGB', flags=ImageCms.Flags.NOOPTIMIZE)
                        self.assertEqual(proof.tobytes(), reference.tobytes())
            # A printer's nonzero black must survive the screen conversion.
            printer = engine.load_profile(paths[0])
            _, proof = engine.previews(Image.new('RGB',(1,1)), srgb, srgb, printer, srgb, 1, True, False)
            self.assertGreater(max(proof.getpixel((0,0))), 10)

if __name__ == '__main__':
    unittest.main()
