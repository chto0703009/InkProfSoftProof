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

PROJECTIONS = ((1, 2), (1, 0), (2, 0))


def lab_values(profile, values):
    mode = profile_mode(profile)
    channels = {'RGB': 3, 'CMYK': 4, 'L': 1, 'LAB': 3}[mode]
    values = np.ascontiguousarray(values, dtype=np.uint8).reshape(-1, channels)
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
            values[:, 0] *= 100 / 255
            values[:, 1:] -= 128
            input_type = LAB_DBL
        else:
            input_type = ({'RGB': 4, 'CMYK': 6, 'L': 3}[mode] << 16) | (channels << 3) | 1
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
    key = hashlib.sha256(b'gamut-v1-absolute-grid' + profile.tobytes()).hexdigest()
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
        lab = lab_values(profile, [raw])[0]
        if first is None:
            first = lab
        result['points'].append(dict(role=role, channels=raw, mode=sample.mode,
                                     lab=lab.tolist(), deltaE76=float(np.linalg.norm(lab-first))))
    return result
