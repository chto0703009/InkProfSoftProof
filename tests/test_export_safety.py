# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
import ast
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageCms
TOOLS=Path(__file__).resolve().parents[1]/'tools'
sys.path.insert(0,str(TOOLS))
from icc_processing import save_image
from softproof_engine import load_image

class ExportSafetyTests(unittest.TestCase):
    def test_new_export_obeys_umask_and_replacement_preserves_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); original=root/'original.png'; target=root/'export.png'
            image=Image.new('RGB',(2,2));image.info['icc_profile']=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes();image.save(original)
            previous=os.umask(0o027)
            try: save_image(image,target,original)
            finally: os.umask(previous)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o640)
            target.chmod(0o600);save_image(image,target,original)
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o600)
            self.assertFalse(list(root.glob('.softprof-*')))

    def test_sigterm_unwinds_export_cleanup(self):
        with tempfile.TemporaryDirectory() as folder:
            script='''
import os,signal,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from icc_processing import save_image
from softproof_engine import terminate_worker
signal.signal(signal.SIGTERM,terminate_worker)
class InterruptedImage:
 mode='RGB'
 info={'icc_profile':b''}
 def save(self,path,**kwargs):
  Path(path).write_bytes(b'partial')
  os.kill(os.getpid(),signal.SIGTERM)
root=Path(sys.argv[2]);(root/'original.png').write_bytes(b'original')
(root/'export.png').write_bytes(b'previous export')
save_image(InterruptedImage(),root/'export.png',root/'original.png')
'''
            process=subprocess.run([sys.executable,'-c',script,str(TOOLS),folder],capture_output=True)
            self.assertEqual(process.returncode,143,process.stderr)
            root=Path(folder)
            self.assertEqual((root/'export.png').read_bytes(),b'previous export')
            self.assertFalse(list(root.glob('.softprof-*')))

    def test_palette_png_preserves_profile_pixels_and_transparency(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'palette.png'
            image=Image.new('P',(2,1));image.putpalette([255,0,0,0,255,0]+[0]*762);image.putdata([0,1])
            profile=ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB')).tobytes()
            for transparency in (None,0):
                kwargs={} if transparency is None else {'transparency':transparency}
                image.save(path,icc_profile=profile,**kwargs)
                result,_,embedded=load_image(path)
                self.assertTrue(embedded);self.assertEqual(result.info['icc_profile'],profile)
                self.assertEqual(result.mode,'RGB' if transparency is None else 'RGBA')
                self.assertEqual(result.getpixel((1,0))[:3],(0,255,0))
                if transparency is not None:self.assertEqual(result.getpixel((0,0))[3],0)

    def test_all_static_16bit_errors_have_english_translations(self):
        catalog=json.loads((TOOLS/'softproof.en.json').read_text())
        for node in ast.walk(ast.parse((TOOLS/'image16.py').read_text())):
            if isinstance(node,ast.Raise) and isinstance(node.exc,ast.Call):
                for arg in node.exc.args:
                    if isinstance(arg,ast.Constant) and isinstance(arg.value,str):
                        self.assertIn(arg.value,catalog)
                        self.assertNotEqual(arg.value,catalog[arg.value])
