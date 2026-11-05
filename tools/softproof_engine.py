#!/usr/bin/env python3
# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""JSON worker for the Python macOS soft-proof viewer (LittleCMS via Pillow)."""
import io
import json
import sys
from pathlib import Path
from PIL import Image, ImageCms, ImageOps
from icc_processing import process, profile_mode, save_image


def load_profile(path):
    if path == 'srgb':
        return ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
    raw = Path(path).read_bytes()
    profile = ImageCms.ImageCmsProfile(io.BytesIO(raw))
    profile.inkprof_original_bytes = raw
    return profile


def describe(profile):
    return ImageCms.getProfileDescription(profile).strip()


def load_image(path, source_path=None):
    with Image.open(path) as opened:
        if getattr(opened, 'n_frames', 1) != 1:
            raise ValueError('Bilder med flera sidor eller bildrutor stöds inte.')
        if opened.mode not in ('RGB', 'RGBA', 'CMYK', 'L', 'LA', 'LAB'):
            raise ValueError('Denna version stöder 8 bitar per kanal: RGB, CMYK, gråskala eller Lab. Exportera andra bildtyper först.')
        image = ImageOps.exif_transpose(opened)
        image.load()
    embedded = image.info.get('icc_profile')
    if embedded:
        source = ImageCms.ImageCmsProfile(io.BytesIO(embedded))
    elif source_path:
        source = load_profile(source_path)
    else:
        raise ValueError('Bilden saknar ICC-profil. Välj en källprofil som beskriver bildens RGB-värden.')
    mode = {'RGBA': 'RGB', 'LA': 'L'}.get(image.mode, image.mode)
    if profile_mode(source) != mode:
        raise ValueError('Källprofilens färgrymd stämmer inte med bildens kanaler.')
    return image, source, bool(embedded)


def stage(image, source, working, intent, bpc):
    # Keeping the source space must not introduce a LUT round trip.
    if source.tobytes() == working.tobytes():
        return image.copy()
    return process(image, source, working, profile_mode(working), intent, bpc)


def previews(image, source, working, printer, display, intent, bpc, paper):
    """Source -> working -> proof, with identical settings to saved conversion.

    Display is a tagged delivery space (Display P3), NOT the monitor profile.
    AppKit subsequently converts those tagged images to the current monitor.
    """
    original = process(image, source, display, 'RGB', 1, False)
    staged = stage(image, source, working, intent, bpc)
    if printer is None:
        return original, process(staged, working, display, 'RGB', 1, False)
    alpha = staged.getchannel('A') if staged.mode in ('RGBA', 'LA') else None
    base = staged.convert('RGB' if staged.mode == 'RGBA' else 'L') if alpha is not None else staged
    flags = ImageCms.Flags.SOFTPROOFING
    if bpc:
        flags |= ImageCms.Flags.BLACKPOINTCOMPENSATION
    transform = ImageCms.buildProofTransformFromOpenProfiles(
        working, display, printer, base.mode, 'RGB', renderingIntent=intent,
        proofRenderingIntent=3 if paper else 1, flags=flags)
    proof = ImageCms.applyTransform(base, transform)
    if alpha is not None:
        proof.putalpha(alpha)
    proof.info.clear()
    proof.info['icc_profile'] = display.tobytes()
    return original, proof


def run(request):
    image, source, embedded = load_image(request['image'], request.get('source'))
    working = load_profile(request['working']) if request.get('working') else source
    printer = load_profile(request['printer']) if request.get('printer') else None
    intent, bpc = request.get('intent', 1), request.get('bpc', True)
    if intent not in (0, 1, 3):
        raise ValueError('Ogiltig återgivningsmetod.')
    metadata = dict(width=image.width, height=image.height, mode=image.mode,
                    source=describe(source), embedded=embedded, working=describe(working),
                    printer=describe(printer) if printer else None)
    if request.get('action') == 'gamut':
        from gamut_analysis import analyze
        analysis = analyze(image, source, working, printer, intent, bpc,
                           request.get('pixel'), request.get('gamutCache'))
        return dict(ok=True, **metadata, **analysis)
    if request.get('action') == 'save':
        if printer is None:
            raise ValueError('Välj skrivarprofil före export.')
        staged = stage(image, source, working, intent, bpc)
        result = process(staged, working, printer, profile_mode(printer), intent, bpc)
        # Preserve the selected ICC file byte-for-byte. LittleCMS may rewrite
        # legacy description tags when a previously inspected profile is saved.
        if hasattr(printer, 'inkprof_original_bytes'):
            result.info['icc_profile'] = printer.inkprof_original_bytes
        save_image(result, request['destination'], request['image'], image.info.get('dpi'))
        return dict(ok=True, **metadata, destination=request['destination'])
    display = load_profile(request['display'])
    # Bound computation and file sizes. Original dimensions are retained for zoom.
    image.thumbnail((2000, 2000), Image.Resampling.LANCZOS)
    original, proof = previews(image, source, working, printer, display, intent, bpc,
                               request.get('paper', False))
    folder = Path(request['output'])
    folder.mkdir(parents=True, exist_ok=True)
    for name, preview in [('original', original), ('proof', proof)]:
        preview.save(folder / (name + '.png'), icc_profile=display.tobytes())
    return dict(ok=True, **metadata, previewWidth=image.width, previewHeight=image.height)


def main():
    request_path, response_path = map(Path, sys.argv[1:3])
    try:
        response = run(json.loads(request_path.read_text()))
    except Exception as error:
        response = dict(ok=False, error=str(error))
    response_path.write_text(json.dumps(response, ensure_ascii=False))
    return 0 if response['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
