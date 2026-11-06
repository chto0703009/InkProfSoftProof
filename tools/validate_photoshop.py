#!/usr/bin/env python3
# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare synthetic RGB/CMYK conversions with installed Photoshop.

Uses only generated documents. Restores active document and displayDialogs.
This measures profile conversions, not Photoshop's on-screen Proof Colors.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image
import softproof_engine as engine
from gamut_analysis import lab_values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--photoshop', default='/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app')
    parser.add_argument('--printer', action='append', required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory for synthetic fixtures and report')
    args = parser.parse_args()
    root = args.output.resolve(); root.mkdir(parents=True, exist_ok=False)
    import AppKit as A
    display_path = root/'display.icc'
    display_path.write_bytes(bytes(A.NSColorSpace.displayP3ColorSpace().ICCProfileData()))
    display = engine.load_profile(display_path)
    source = engine.load_profile('srgb')
    image = Image.new('RGB',(125,1)); image.putdata(list(itertools.product((0,32,128,224,255), repeat=3)))
    source_path = root/'synthetic.tif'; image.save(source_path, icc_profile=source.tobytes())
    jobs=[]; profiles=[]
    for path in args.printer:
        p = engine.load_profile(path); profiles.append(p)
        for intent,bpc in itertools.product((0,1,3),(False,True)):
            jobs.append(dict(index=len(jobs),profile=engine.describe(p),profileIndex=len(profiles)-1,intent=intent,bpc=bpc))
    data=json.dumps(dict(root=str(root),source=str(source_path),jobs=jobs))
    script='''(function(){
var cfg=CONFIG, oldDialogs=app.displayDialogs, previous=app.documents.length?app.activeDocument:null, doc=null, copy=null;
function save(d,path){var options=new TiffSaveOptions();options.embedColorProfile=true;options.imageCompression=TIFFEncoding.NONE;d.saveAs(new File(path),options,true,Extension.LOWERCASE);}
try { app.displayDialogs=DialogModes.NO;
var intents=[Intent.PERCEPTUAL,Intent.RELATIVECOLORIMETRIC,null,Intent.ABSOLUTECOLORIMETRIC];
for(var i=0;i<cfg.jobs.length;i++) {var j=cfg.jobs[i],prefix=cfg.root+'/'+j.index;
 doc=app.open(new File(cfg.source));doc.convertProfile(j.profile,intents[j.intent],j.bpc,false);save(doc,prefix+'-printer.tif');
 for(var k=0;k<3;k++){copy=doc.duplicate('SoftProf synthetic validation');copy.convertProfile('Display P3',k==2?Intent.ABSOLUTECOLORIMETRIC:Intent.RELATIVECOLORIMETRIC,k==0,false);save(copy,prefix+'-proof-'+k+'.tif');copy.close(SaveOptions.DONOTSAVECHANGES);copy=null;}
 doc.close(SaveOptions.DONOTSAVECHANGES);doc=null;
}
return app.version;
}finally{if(copy)copy.close(SaveOptions.DONOTSAVECHANGES);if(doc)doc.close(SaveOptions.DONOTSAVECHANGES);app.displayDialogs=oldDialogs;if(previous)app.activeDocument=previous;}
})();'''.replace('CONFIG', data)
    jsx=root/'compare.jsx';jsx.write_text(script)
    # Pass paths as structured AppleScript argv, never interpolate shell code.
    applescript='on run argv\n using terms from application "/Applications/Adobe Photoshop 2026/Adobe Photoshop 2026.app"\n tell application (item 1 of argv)\n return do javascript file (item 2 of argv)\n end tell\n end using terms from\nend run'
    result=subprocess.run(['osascript','-e',applescript,args.photoshop,str(jsx)],capture_output=True,text=True,timeout=240)
    if result.returncode: raise RuntimeError(result.stderr)
    report=dict(scope='Synthetic 8-bit profile conversions; not a visual or Proof Colors screen validation',photoshop=result.stdout.strip(),patches=125,profiles=[dict(description=engine.describe(p),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest()) for p,path in zip(profiles,args.printer)],cases=[])
    def metrics(actual, reference, profile):
        a=np.array(actual);b=np.array(reference);diff=np.abs(a.astype(int)-b.astype(int))
        delta=np.linalg.norm(lab_values(profile,a.reshape(-1,a.shape[-1]))-lab_values(profile,b.reshape(-1,b.shape[-1])),axis=1)
        return dict(maxChannelDifference=int(diff.max()),meanAbsoluteChannelDifference=float(diff.mean()),meanDeltaE76=float(delta.mean()),maxDeltaE76=float(delta.max()))
    for j in jobs:
        p=profiles[j['profileIndex']];intent=j['intent'];bpc=j['bpc'];prefix=root/str(j['index'])
        converted=engine.process(image,source,p,engine.profile_mode(p),intent,bpc)
        with Image.open(str(prefix)+'-printer.tif') as reference:
            printer_metrics=metrics(converted,reference,p)
        row=dict(profile=j['profile'],intent=intent,bpc=bpc,printer=printer_metrics,proof={})
        for k,(paper,ink) in enumerate(((False,False),(False,True),(True,True))):
            _,proof=engine.previews(image,source,source,p,display,intent,bpc,paper,ink)
            with Image.open(str(prefix)+f'-proof-{k}.tif') as reference:
                row['proof'][('normalised','blackInk','paperAndInk')[k]]=metrics(proof,reference,display)
        report['cases'].append(row)
    (root/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(root/'report.json')

if __name__=='__main__': main()
