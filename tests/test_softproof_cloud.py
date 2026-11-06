# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
import sys
from pathlib import Path
import unittest
import numpy as np
from PIL import Image, ImageCms
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from gamut_analysis import colour_cloud, lab_values
import softproof_engine as engine


class CloudTests(unittest.TestCase):
    def setUp(self):
        self.srgb=engine.load_profile('srgb')

    def test_frequency_and_actual_representatives(self):
        im=Image.new('RGB',(100,1));im.putdata([(255,0,0)]*90+[(0,0,255)]*10)
        cloud=colour_cloud(im,self.srgb,self.srgb,None,1,False)
        self.assertEqual(cloud['counts'],[90,10])
        self.assertEqual(cloud['stages'][0]['rgb'],[[255,0,0],[0,0,255]])
        self.assertAlmostEqual(cloud['stages'][0]['lab'][0][0],54.29,places=1)
        self.assertEqual(cloud['sampled'],100)

    def test_bins_use_real_pixel_not_average(self):
        im=Image.new('RGB',(2,1));im.putdata([(17,17,17),(30,30,30)])
        cloud=colour_cloud(im,self.srgb,self.srgb,None,1,False)
        self.assertEqual(cloud['counts'],[2])
        self.assertEqual(cloud['stages'][0]['rgb'],[[17,17,17]])

    def test_identity_survives_settings_and_conversions_match_export(self):
        im=Image.new('RGB',(3,1));im.putdata([(190,35,81),(211,14,82),(130,80,210)])
        lab=ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
        first=colour_cloud(im,self.srgb,self.srgb,self.srgb,1,False)
        second=colour_cloud(im,self.srgb,lab,self.srgb,0,True)
        self.assertEqual(first['ids'],second['ids'])
        self.assertEqual(first['identity'],second['identity'])
        self.assertEqual(first['counts'],second['counts'])
        for rgb,position in zip(second['stages'][0]['rgb'],second['stages'][2]['lab']):
            pixel=Image.new('RGB',(1,1),tuple(rgb))
            staged=engine.stage(pixel,self.srgb,lab,0,True)
            printed=engine.process(staged,lab,self.srgb,'RGB',0,True)
            expected=lab_values(self.srgb,[printed.getpixel((0,0))])[0]
            np.testing.assert_allclose(position,expected,atol=1e-8)
        self.assertFalse(np.allclose(first['stages'][1]['lab'],second['stages'][1]['lab']))

    def test_alpha_and_empty_image(self):
        im=Image.new('RGBA',(3,1));im.putdata([(255,0,0,255),(255,0,0,128),(0,255,0,0)])
        cloud=colour_cloud(im,self.srgb,self.srgb,None,1,False)
        self.assertAlmostEqual(cloud['counts'][0],1+128/255)
        self.assertEqual(len(cloud['ids']),1)
        empty=colour_cloud(Image.new('RGBA',(2,2)),self.srgb,self.srgb,None,1,False)
        self.assertEqual(empty['ids'],[]);self.assertEqual(empty['stages'],[])

    def test_bounded_deterministic_sampling_and_new_image_identity(self):
        im=Image.new('RGB',(500,20));im.putdata([(i%256,(i//3)%256,(i//7)%256) for i in range(10000)])
        a=colour_cloud(im,self.srgb,self.srgb,None,1,False,max_samples=100,max_points=8)
        b=colour_cloud(im,self.srgb,self.srgb,None,1,False,max_samples=100,max_points=8)
        self.assertEqual(a,b);self.assertEqual(a['sampled'],100);self.assertLessEqual(len(a['ids']),8)
        c=colour_cloud(Image.new('RGB',(500,20),(255,255,255)),self.srgb,self.srgb,None,1,False,max_samples=100,max_points=8)
        self.assertNotEqual(a['identity'],c['identity'])

if __name__=='__main__': unittest.main()
