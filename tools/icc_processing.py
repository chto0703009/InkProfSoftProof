# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""GUI-independent ICC conversion and atomic image export."""
import os
from pathlib import Path
import tempfile
from PIL import Image, ImageCms

INTENTS = {'Relativ kolorimetrisk': 1, 'Absolut kolorimetrisk': 3, 'Perceptuell': 0}
MODES = {'RGB': 'RGB', 'CMYK': 'CMYK', 'Gråskala': 'L', 'Lab': 'LAB'}

def profile_mode(profile):
    space = profile.profile.xcolor_space.strip()
    modes = {'RGB': 'RGB', 'CMYK': 'CMYK', 'GRAY': 'L', 'Lab': 'LAB'}
    if space not in modes:
        raise ValueError(f'Profilens färgrymd stöds inte: {space}')
    return modes[space]

def process(image, source, target, mode, intent, bpc, assign=False):
    """Never infer a source profile or silently convert untagged pixels."""
    alpha = image.getchannel('A') if image.mode in ('RGBA', 'LA') else None
    base = image.convert('RGB' if image.mode == 'RGBA' else 'L') if alpha else image.copy()
    if base.mode not in ('RGB', 'CMYK', 'L', 'LAB'):
        raise ValueError('Endast 8-bitars RGB, CMYK, gråskala och Lab stöds. Exportera andra bildtyper först.')
    if assign:
        if profile_mode(target) != base.mode or mode != base.mode:
            raise ValueError('Vid tilldelning måste profilens färgrymd och vald färgrymd motsvara bildens kanaler.')
        result = base
    else:
        if source is None:
            raise ValueError('Bilden saknar ICC-profil. Välj en källprofil först.')
        if profile_mode(source) != base.mode:
            raise ValueError('Källprofilens färgrymd motsvarar inte bildens kanaler.')
        if profile_mode(target) != mode:
            raise ValueError('Vald färgrymd måste motsvara målprofilens färgrymd.')
        # Avoid LCMS's extra 8-bit precomputed optimisation grid. It can
        # introduce substantial dark-tone errors with some printer LUTs.
        flags = ImageCms.Flags.NOOPTIMIZE
        if bpc: flags |= ImageCms.Flags.BLACKPOINTCOMPENSATION
        if getattr(base,'bits',8)==16:
            from image16 import transform16
            result=transform16(base,source,target,mode,intent,bpc)
        else:
            result = ImageCms.profileToProfile(base, source, target, renderingIntent=intent,
                                              outputMode=mode, flags=flags)
    if alpha is not None:
        if result.mode not in ('RGB', 'L'):
            raise ValueError('Transparens kan endast bevaras för RGB eller gråskala.')
        result.putalpha(alpha)
    result.info.clear()
    result.info['icc_profile'] = target.tobytes()
    return result

def save_image(image, destination, original, dpi=None):
    destination = Path(destination)
    if destination.resolve() == Path(original).resolve() or (destination.exists() and os.path.samefile(destination, original)):
        raise ValueError('Välj ett annat filnamn än originalbildens.')
    suffix = destination.suffix.lower()
    fmt = {'.tif': 'TIFF', '.tiff': 'TIFF', '.png': 'PNG', '.jpg': 'JPEG', '.jpeg': 'JPEG'}.get(suffix)
    if not fmt:
        raise ValueError('Välj TIFF, PNG eller JPEG som filändelse.')
    allowed = {'TIFF': ('RGB', 'RGBA', 'CMYK', 'L', 'LA', 'LAB'), 'PNG': ('RGB', 'RGBA', 'L', 'LA'), 'JPEG': ('RGB', 'CMYK', 'L')}
    if image.mode not in allowed[fmt]:
        raise ValueError(f'{fmt} stöder inte {image.mode}. Välj TIFF eller en annan färgrymd.')
    if getattr(image,'bits',8)==16 and fmt=='JPEG':
        raise ValueError('16-bitarsbilder måste sparas som TIFF eller PNG. JPEG stöder bara 8 bitar.')
    options = {'icc_profile': image.info['icc_profile']}
    if dpi:
        options['dpi'] = dpi
    if fmt == 'JPEG':
        options.update(quality=100, subsampling=0)
    if fmt == 'TIFF':
        options['compression'] = 'tiff_lzw'
    fd, temporary = tempfile.mkstemp(prefix='.inkprof-', dir=destination.parent)
    os.close(fd)
    try:
        image.save(temporary, format=fmt, **options)
        os.replace(temporary, destination)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
