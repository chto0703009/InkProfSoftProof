# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Precision, format metadata and end-to-end checks for uint16 rasters."""
import io
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
import tifffile
import imagecodecs
from PIL import ImageCms
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from image16 import Image16
import softproof_engine as engine
from gamut_analysis import analyze,colour_cloud,lab_values


class SixteenBitTests(unittest.TestCase):
    def setUp(self):
        self.profile=engine.load_profile('srgb')
        self.data=np.array([[[4660,22136,39612],[4863,22271,39679],[65535,32768,1]],[[7,8,9],[256,257,258],[0,65535,0]]],dtype=np.uint16)
        self.image=Image16(self.data,'RGB',{'icc_profile':self.profile.tobytes(),'dpi':(300,240)})

    def test_tiff_and_png_roundtrip_preserve_low_bits_icc_and_dpi(self):
        with tempfile.TemporaryDirectory() as directory:
            for suffix in ('tif','png'):
                with self.subTest(format=suffix):
                    path=Path(directory)/('image.'+suffix);self.image.save(path)
                    loaded,profile,embedded=engine.load_image(path)
                    self.assertTrue(embedded);self.assertEqual(loaded.bits,16)
                    np.testing.assert_array_equal(loaded.array,self.data)
                    self.assertEqual(profile.tobytes(),self.profile.tobytes())
                    self.assertAlmostEqual(loaded.info['dpi'][0],300,places=1)
                    if suffix=='tif':
                        with tifffile.TiffFile(path) as f:self.assertEqual(f.pages[0].bitspersample,16)
                    else:self.assertEqual(path.read_bytes()[24],16)

    def test_compression_planar_byte_order_and_orientation(self):
        with tempfile.TemporaryDirectory() as directory:
            for compression in ('lzw','deflate','packbits'):
                path=Path(directory)/(compression+'.tif')
                tifffile.imwrite(path,np.moveaxis(self.data,-1,0),photometric='rgb',planarconfig='separate',byteorder='>',compression=compression,iccprofile=self.profile.tobytes(),extratags=[(274,'H',1,6,False)])
                loaded,_,_=engine.load_image(path)
                np.testing.assert_array_equal(loaded.array,np.rot90(self.data,3))

    def test_transform_retains_more_than_256_levels(self):
        values=np.arange(65536,dtype=np.uint16)
        image=Image16(np.repeat(values[None,:,None],3,axis=2),'RGB')
        output=engine.process(image,self.profile,self.profile,'RGB',1,False)
        self.assertEqual(len(np.unique(output.array[:,:,0])),65536)
        np.testing.assert_array_equal(output.array,image.array)

    def test_exact_pixel_and_cloud_use_original_16bit_values(self):
        result=analyze(self.image,self.profile,self.profile,self.profile,1,False,[1,0])
        self.assertEqual(result['points'][0]['channels'],[4863,22271,39679])
        expected=lab_values(self.profile,[[4863,22271,39679]],bits=16)[0]
        np.testing.assert_allclose(result['points'][0]['lab'],expected,atol=1e-8)
        cloud=colour_cloud(self.image,self.profile,self.profile,None,1,False)
        self.assertGreater(len(cloud['ids']),0)
        self.assertEqual(cloud['sampled'],6)
        for stage in cloud['stages']: self.assertTrue(np.isfinite(stage['lab']).all())

    def test_low_bits_remain_visible_to_colourimetry(self):
        values=np.array([[20050+i]*3 for i in range(100)],dtype=np.uint16)
        lab=lab_values(self.profile,values,bits=16)
        self.assertTrue(np.all(np.diff(lab[:,0])>0))
        # All these values would collapse into a single 8-bit gray code.
        self.assertEqual(len(np.unique(values[:,0]//257)),1)

    def test_lab_working_space_retains_16bit_precision(self):
        lab=ImageCms.ImageCmsProfile(ImageCms.createProfile('LAB'))
        image=Image16(np.array([[[65535]*3]],dtype=np.uint16),'RGB')
        converted=engine.process(image,self.profile,lab,'LAB',1,False)
        result=lab_values(lab,[converted.getpixel((0,0))],bits=16)[0]
        np.testing.assert_allclose(result,[100,0,0],atol=.001)
        back=engine.process(converted,lab,self.profile,'RGB',1,False)
        self.assertGreaterEqual(min(back.getpixel((0,0))),65533)

    def test_alpha_preserved_and_frequency_uses_full_scale(self):
        values=np.dstack((self.data,np.array([[65535,32768,0],[1,20000,60000]],dtype=np.uint16)))
        image=Image16(values,'RGBA',self.image.info)
        converted=engine.process(image,self.profile,self.profile,'RGB',1,False)
        np.testing.assert_array_equal(converted.array[:,:,-1],values[:,:,-1])
        sample=analyze(image,self.profile,self.profile,None,1,False,[1,0])
        self.assertEqual(sample['alphaMax'],65535);self.assertEqual(sample['alpha'],32768)
        cloud=colour_cloud(image,self.profile,self.profile,None,1,False)
        self.assertAlmostEqual(sum(cloud['counts']),values[:,:,-1].sum()/65535)
        with tempfile.TemporaryDirectory() as directory:
            for extension in ('tif','png'):
                path=Path(directory)/('alpha.'+extension);converted.save(path)
                loaded,_,_=engine.load_image(path)
                np.testing.assert_array_equal(loaded.array,converted.array)

    def test_associated_alpha_is_unpremultiplied(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'premult.tif'
            values=np.array([[[10000,5000,2500,32768]]],dtype=np.uint16)
            tifffile.imwrite(path,values,photometric='rgb',extrasamples='assocalpha',iccprofile=self.profile.tobytes())
            image,_,_=engine.load_image(path)
            np.testing.assert_allclose(image.getpixel((0,0)),[20000,10000,5000,32768],atol=1)

    def test_full_pipeline_preview_export_and_source_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'source.tif';profile=root/'srgb.icc'
            self.image.save(source);before=source.read_bytes();profile.write_bytes(self.profile.tobytes())
            request=dict(image=str(source),printer=str(profile),display=str(profile),output=str(root/'preview'),intent=1,bpc=False)
            response=engine.run(request);self.assertEqual(response['bits'],16)
            for name in ('original','proof'):
                image,_,_=engine.load_image(root/'preview'/f'{name}.png')
                np.testing.assert_array_equal(image.array,self.data)
            for suffix in ('tif','png'):
                destination=root/('export.'+suffix)
                engine.run(dict(request,action='save',destination=str(destination)))
                image,_,_=engine.load_image(destination)
                np.testing.assert_array_equal(image.array,self.data)
            with self.assertRaisesRegex(ValueError,'JPEG'):
                engine.run(dict(request,action='save',destination=str(root/'out.jpg')))
            with self.assertRaisesRegex(ValueError,'originalbildens'):
                engine.run(dict(request,action='save',destination=str(source)))
            self.assertEqual(before,source.read_bytes())

    def test_cmyk_16bit_export_and_analysis(self):
        path=Path('/Library/ColorSync/Profiles/ISOcoated_v2_eci.icc')
        if not path.exists(): self.skipTest('Requires installed CMYK printer fixture')
        printer=engine.load_profile(path)
        converted=engine.process(self.image,self.profile,printer,'CMYK',1,True)
        self.assertEqual(converted.array.dtype,np.uint16)
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'cmyk.tif';converted.save(dest)
            actual,profile,_=engine.load_image(dest)
            self.assertEqual(actual.mode,'CMYK')
            np.testing.assert_array_equal(actual.array,converted.array)
            cloud=colour_cloud(actual,profile,profile,None,1,False)
            self.assertTrue(cloud['stages'][0]['lab'])

    def test_gray_16bit_and_white_is_zero(self):
        path=Path('/System/Library/ColorSync/Profiles/Generic Gray Gamma 2.2 Profile.icc')
        if not path.exists(): self.skipTest('Requires system gray profile')
        profile=engine.load_profile(path)
        gray=np.array([[0,1,10000,65535]],dtype=np.uint16)
        with tempfile.TemporaryDirectory() as directory:
            filename=Path(directory)/'gray.tif'
            tifffile.imwrite(filename,gray,photometric='miniswhite',iccprofile=profile.tobytes())
            loaded,source,_=engine.load_image(filename)
            self.assertEqual(loaded.mode,'L')
            np.testing.assert_array_equal(loaded.array[:,:,0],65535-gray)
            converted=engine.process(loaded,source,self.profile,'RGB',1,False)
            self.assertEqual(converted.bits,16)
            sample=analyze(loaded,source,source,None,1,False,[2,0])
            self.assertEqual(sample['points'][0]['channels'],[55535])
            cloud=colour_cloud(loaded,source,source,None,1,False)
            self.assertTrue(cloud['stages'][0]['lab'])

    def test_float_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'float.tif'
            tifffile.imwrite(path,np.zeros((2,2),dtype=np.float32),photometric='minisblack')
            with self.assertRaisesRegex(ValueError,'32 bitar|flyttal'):
                engine.load_image(path,'srgb')

if __name__=='__main__':unittest.main()
