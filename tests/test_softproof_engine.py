# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Run with .venv/bin/python -m unittest discover -s tests -p test_softproof_engine.py."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageCms

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
import softproof_engine as engine


class SoftProofTests(unittest.TestCase):
    def setUp(self):
        self.srgb = engine.load_profile('srgb')
        self.lab = ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
        self.image = Image.new('RGB', (12, 12), (130, 80, 210))

    def test_preserve_source_does_not_roundtrip(self):
        with patch.object(engine, 'process', side_effect=AssertionError('Unexpected conversion')):
            result = engine.stage(self.image, self.srgb, self.srgb, 0, True)
        self.assertEqual(result.tobytes(), self.image.tobytes())

    def test_all_intents_and_bpc_and_paper(self):
        for intent in (0, 1, 3):
            for bpc in (False, True):
                for paper in (False, True):
                    original, proof = engine.previews(self.image, self.srgb, self.srgb, self.srgb, self.srgb, intent, bpc, paper)
                    self.assertEqual(proof.mode, 'RGB')
                    self.assertEqual(proof.info['icc_profile'], self.srgb.tobytes())
                    self.assertEqual(original.tobytes(), self.image.tobytes())

    def test_alpha_survives(self):
        image = self.image.convert('RGBA')
        image.putalpha(112)
        original, proof = engine.previews(image, self.srgb, self.srgb, self.srgb, self.srgb, 1, True, False)
        self.assertEqual(proof.getchannel('A').getextrema(), (112, 112))
        self.assertEqual(original.getchannel('A').getextrema(), (112, 112))

    def test_missing_profile_requires_explicit_source(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'image.png'
            self.image.save(path)
            with self.assertRaisesRegex(ValueError, 'saknar ICC'):
                engine.load_image(path)
            _, profile, embedded = engine.load_image(path, 'srgb')
            self.assertFalse(embedded)
            self.assertEqual(engine.profile_mode(profile), 'RGB')

    def test_embedded_profile_wins_over_fallback(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'image.png'
            self.image.save(path, icc_profile=self.srgb.tobytes())
            _, profile, embedded = engine.load_image(path, '/does/not/exist.icc')
            self.assertTrue(embedded)
            self.assertEqual(profile.tobytes(), self.srgb.tobytes())

    def test_save_full_resolution_printer_profile_and_original_protection(self):
        with tempfile.TemporaryDirectory() as folder:
            original = Path(folder) / 'source.tif'
            dest = Path(folder) / 'out.tif'
            self.image.save(original, icc_profile=self.srgb.tobytes())
            before = original.read_bytes()
            labfile = Path(folder) / 'lab.icc'
            labfile.write_bytes(self.lab.tobytes())
            request = dict(image=str(original), printer=str(labfile), action='save', destination=str(dest), paper=True)
            engine.run(request)
            with Image.open(dest) as result:
                self.assertEqual(result.size, self.image.size)
                self.assertEqual(result.mode, 'LAB')
                self.assertEqual(result.info['icc_profile'], self.lab.tobytes())
            first = dest.read_bytes()
            request['paper'] = False
            engine.run(request)
            self.assertEqual(dest.read_bytes(), first)
            request['destination'] = str(original)
            with self.assertRaisesRegex(ValueError, 'originalbildens'):
                engine.run(request)
            self.assertEqual(original.read_bytes(), before)

    def test_wrong_source_channel_count_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'gray.png'
            self.image.convert('L').save(path)
            with self.assertRaisesRegex(ValueError, 'kanaler'):
                engine.load_image(path, 'srgb')


class GamutTests(unittest.TestCase):
    def setUp(self):
        import gamut_analysis
        self.gamut = gamut_analysis
        self.srgb = engine.load_profile('srgb')

    def test_lab_uses_d50_float_colorimetry(self):
        white, black, red = self.gamut.lab_values(self.srgb, [[255,255,255], [0,0,0], [255,0,0]])
        self.assertAlmostEqual(white[0], 100, places=3)
        self.assertLess(abs(white[1])+abs(white[2]), 0.01)
        self.assertAlmostEqual(black[0], 0, places=3)
        self.assertAlmostEqual(red[0], 54.29, places=1)
        self.assertAlmostEqual(red[1], 80.81, places=1)

    def test_sample_is_original_pixel_not_resized_preview(self):
        image = Image.new('RGB', (2501, 2), (0,0,0))
        image.putpixel((2456, 1), (211,14,82))
        result = self.gamut.analyze(image, self.srgb, self.srgb, self.srgb, 1, False, [2456,1])
        self.assertEqual(result['pixel'], [2456,1])
        self.assertEqual([p['channels'] for p in result['points']], [[211,14,82]]*3)
        self.assertTrue(all(p['deltaE76'] == 0 for p in result['points']))

    def test_sample_matches_export_conversion(self):
        lab = ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
        image = Image.new('RGB', (1,1), (190,35,81))
        result = self.gamut.analyze(image, self.srgb, lab, self.srgb, 0, True, [0,0])
        staged = engine.stage(image, self.srgb, lab, 0, True)
        printed = engine.process(staged, lab, self.srgb, 'RGB', 0, True)
        self.assertEqual(result['points'][1]['channels'], list(staged.getpixel((0,0))))
        self.assertEqual(result['points'][2]['channels'], list(printed.getpixel((0,0))))
        self.assertTrue(all(len(p['lab']) == 3 for p in result['points']))

    def test_profile_cache_and_ab_projection(self):
        with tempfile.TemporaryDirectory() as cache:
            first = self.gamut.profile_gamut(self.srgb, cache)
            self.assertEqual(first['count'], 17**3)
            self.assertEqual(len(first['projections']), 1)
            self.assertTrue(all(len(p)>2 for p in first['projections']))
            with patch.object(self.gamut, 'lab_values', side_effect=AssertionError('Cache miss')):
                self.assertEqual(self.gamut.profile_gamut(self.srgb, cache), first)

    def test_hull_handles_gray_and_duplicate_points(self):
        self.assertEqual(self.gamut.convex_envelope([[0,0],[0,0],[0,1],[0,2]]), [[0,0],[0,2]])
        self.assertEqual(len(self.gamut.convex_envelope([[0,0],[1,0],[1,1],[0,1],[0.5,0.5]])), 4)

    def test_bounds_and_alpha(self):
        image = Image.new('RGBA', (1,1), (20,40,60,70))
        with self.assertRaisesRegex(ValueError, 'utanför'):
            self.gamut.analyze(image, self.srgb, self.srgb, None, 1, True, [1,0])
        result = self.gamut.analyze(image, self.srgb, self.srgb, None, 1, True, [0,0])
        self.assertEqual(result['alpha'], 70)
        self.assertEqual(result['points'][0]['channels'], [20,40,60])


if __name__ == '__main__':
    unittest.main()
