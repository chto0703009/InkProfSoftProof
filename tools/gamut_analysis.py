# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Sampled ICC gamut projections and exact-pixel conversion path in Lab D50.

Contours are convex outer envelopes of device-grid samples, not exact gamut
boundaries or an in/out test. Lab is evaluated through LittleCMS double output;
the device pixels themselves follow the application's 8-bit export pipeline.
"""
import ctypes as C
import hashlib
import itertools
import json
import sys
from pathlib import Path
import numpy as np
from icc_processing import process, profile_mode

if not getattr(sys, 'frozen', False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'analysis'))
from lcms_float import LittleCMS, LAB_DBL

PROJECTIONS = ((1, 2),)  # a*/b* seen from above


def lab_values(profile, values, bits=8):
    mode = profile_mode(profile)
    channels = {'RGB': 3, 'CMYK': 4, 'L': 1, 'LAB': 3}[mode]
    values = np.ascontiguousarray(values, dtype=np.uint16 if bits==16 else np.uint8).reshape(-1, channels)
    output = np.empty((len(values), 3), dtype=np.float64)
    cms = LittleCMS()
    lib = cms.lib
    handles, transform = [], None
    try:
        data = profile.tobytes()
        buffer = C.create_string_buffer(data)
        src = lib.cmsOpenProfileFromMem(buffer, len(data))
        if not src:
            raise ValueError('ICC-profilen kunde inte öppnas för färgomfångsanalys.')
        handles.append(src)
        dst = lib.cmsCreateLab4Profile(None)
        if not dst:
            raise ValueError('Lab-profilen kunde inte skapas.')
        handles.append(dst)
        if mode == 'LAB':
            # Pillow's public getpixel() uses Lab8 with a*/b* offset by 128.
            values = values.astype(np.float64)
            values[:, 0] *= 100 / (65535 if bits==16 else 255)
            if bits==16: values[:, 1:] *= 255/65535
            values[:, 1:] -= 128
            input_type = LAB_DBL
        else:
            input_type = ({'RGB': 4, 'CMYK': 6, 'L': 3}[mode] << 16) | (channels << 3) | (2 if bits==16 else 1)
        # Fixed absolute colorimetry, no BPC: compare all stages in physical D50
        # coordinates, independently of the selected conversion/proof intent.
        transform = lib.cmsCreateTransform(src, input_type, dst, LAB_DBL, 3, 0x0100 | 0x0040)
        if not transform:
            raise ValueError('Profilen stöder inte enhetsvärden till Lab för analys.')
        lib.cmsDoTransform(transform, values.ctypes.data, output.ctypes.data, len(values))
        if not np.isfinite(output).all():
            raise ValueError('ICC-profilen gav ogiltiga Lab-värden.')
        return output
    finally:
        if transform:
            lib.cmsDeleteTransform(transform)
        for handle in reversed(handles):
            lib.cmsCloseProfile(handle)


def convex_envelope(points):
    """Monotonic-chain hull, including degenerate gray profiles."""
    points = sorted(set(map(tuple, points)))
    if len(points) < 3:
        return [list(point) for point in points]
    def cross(o, a, b):
        return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lower, upper = [], []
    for target, sequence in ((lower, points), (upper, reversed(points))):
        for point in sequence:
            while len(target) >= 2 and cross(target[-2], target[-1], point) <= 0:
                target.pop()
            target.append(point)
    return [list(point) for point in lower[:-1] + upper[:-1]]


def profile_gamut(profile, cache=None):
    key = hashlib.sha256(b'gamut-v2-absolute-grid-ab' + profile.tobytes()).hexdigest()
    path = Path(cache) / (key + '.json') if cache else None
    if path and path.exists():
        return json.loads(path.read_text())
    mode = profile_mode(profile)
    channels = {'RGB': 3, 'CMYK': 4, 'L': 1, 'LAB': 3}[mode]
    levels = np.rint(np.linspace(0, 255, 9 if mode == 'CMYK' else 17)).astype(int)
    samples = list(itertools.product(levels, repeat=channels))
    lab = lab_values(profile, samples)
    result = dict(mode=mode, count=len(samples), projections=[
        convex_envelope(lab[:, axes].round(5).tolist()) for axes in PROJECTIONS])
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(result))
        temporary.replace(path)
    return result


def analyze(image, source, working, printer, intent, bpc, position=None, cache=None):
    from softproof_engine import stage, describe
    result = dict(profiles=[], points=[])
    for role, profile in [('source', source), ('working', working), ('printer', printer)]:
        if profile:
            result['profiles'].append(dict(role=role, name=describe(profile), **profile_gamut(profile, cache)))
    if position is None:
        return result
    x, y = map(int, position)
    if not (0 <= x < image.width and 0 <= y < image.height):
        raise ValueError('Färgprovet ligger utanför bilden.')
    pixel = image.crop((x, y, x+1, y+1))
    result['pixel'] = [x, y]
    if pixel.mode in ('RGBA', 'LA'):
        result['alpha'] = pixel.getchannel('A').getpixel((0, 0))
        result['alphaMax'] = 65535 if getattr(pixel,'bits',8)==16 else 255
        pixel = pixel.convert('RGB' if pixel.mode == 'RGBA' else 'L')
    staged = stage(pixel, source, working, intent, bpc)
    stages = [('source', pixel, source), ('working', staged, working)]
    if printer:
        printed = process(staged, working, printer, profile_mode(printer), intent, bpc)
        stages.append(('printer', printed, printer))
    first = None
    for role, sample, profile in stages:
        raw = sample.getpixel((0, 0))
        raw = [raw] if isinstance(raw, int) else list(raw)
        lab = lab_values(profile, [raw],bits=getattr(sample,'bits',8))[0]
        if first is None:
            first = lab
        result['points'].append(dict(role=role, channels=raw, mode=sample.mode,
                                     lab=lab.tolist(), deltaE76=float(np.linalg.norm(lab-first))))
    return result


def colour_cloud(image, source, working, printer, intent, bpc, max_samples=65536, max_points=1024, display=None):
    """Stable, frequency-ranked source bins; convert actual representative pixels.

    Deterministic stratified sampling without image interpolation. All stages
    share representatives/IDs so motion compares the same source colours.
    Counts estimate image frequency; transparent samples carry alpha weight.
    """
    from PIL import Image, ImageCms
    from softproof_engine import stage
    mode = image.mode
    bits=getattr(image,'bits',8); maximum=65535 if bits==16 else 255
    channels = len(image.getbands())
    count = image.width * image.height
    size = min(count, max_samples)
    if size == count:
        indices = np.arange(count, dtype=np.int64)
    else:
        # Fixed-seed stratified sampling avoids regular-grid aliasing while
        # retaining identical samples when only conversion settings change.
        edges = np.arange(size+1, dtype=np.int64)*count//size
        indices = edges[:-1]+(np.random.default_rng(0).random(size)*np.diff(edges)).astype(np.int64)
    raw = np.asarray(image).reshape(count, channels)[indices]
    weights = np.ones(len(raw), dtype=float)
    if mode in ('RGBA','LA'):
        weights = raw[:,-1].astype(float)/maximum
        raw = raw[:,:-1]; mode = 'RGB' if mode=='RGBA' else 'L'
    identity = hashlib.sha256(str((image.size,image.mode)).encode()+raw.tobytes()+weights.tobytes()).hexdigest()
    raw, weights = raw[weights>0], weights[weights>0]
    if not len(raw):
        return dict(identity=identity, ids=[], counts=[], sampled=min(count,max_samples), total=count, stages=[])
    # Quantise only for grouping. The chosen representative retains its exact
    # original channels and follows the same conversion chain as image export.
    keys = (raw//(4096 if bits==16 else 16)).astype(np.int64) @ (16**np.arange(raw.shape[1],dtype=np.int64))
    ids, first, inverse = np.unique(keys, return_index=True, return_inverse=True)
    frequencies = np.bincount(inverse, weights=weights)
    selected = np.lexsort((ids,-frequencies))[:max_points]
    values = np.ascontiguousarray(raw[first[selected]], dtype=np.uint16 if bits==16 else np.uint8)
    if bits==16:
        from image16 import Image16
        representative = Image16(values.reshape(1,len(values),-1),mode)
    else:
        representative = Image.frombytes(mode,(len(values),1),values.tobytes())
    staged = stage(representative,source,working,intent,bpc)
    stages = [('source',representative,source),('working',staged,working)]
    if printer:
        stages.append(('printer',process(staged,working,printer,profile_mode(printer),intent,bpc),printer))
    delivery = display or ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
    result=[]
    for role, sample, profile in stages:
        device = np.asarray(sample).reshape(len(values),-1)
        rgb = np.asarray(process(sample,profile,delivery,'RGB',1,False)).reshape(-1,3)
        result.append(dict(role=role,lab=lab_values(profile,device,bits=bits).tolist(),rgb=np.rint(rgb.astype(float)/(257 if bits==16 else 1)).astype(int).tolist()))
    return dict(identity=identity,ids=ids[selected].tolist(),counts=frequencies[selected].tolist(),
                sampled=min(count,max_samples),total=count,representedWeight=float(frequencies[selected].sum()),
                colourSpace='Display P3' if display is not None else 'sRGB', stages=result)
