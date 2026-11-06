# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
# SoftProf is free software under GNU GPL version 3 or later.
# Distributed WITHOUT ANY WARRANTY; see LICENSE and THIRD_PARTY_NOTICES.md.
"""LittleCMS public C API with double RGB/Lab buffers (not Pillow's 8-bit path).
API constants/signatures: LittleCMS lcms2.h, MIT, see THIRD_PARTY_NOTICES.md.
No claim that internal LUT calculations use double precision throughout.
"""
import ctypes as C
import ctypes.util
import os
from pathlib import Path
import numpy as np

RGB_DBL = (1 << 22) | (4 << 16) | (3 << 3)
LAB_DBL = (1 << 22) | (10 << 16) | (3 << 3)

class CIExyY(C.Structure):
    _fields_ = [('x', C.c_double), ('y', C.c_double), ('Y', C.c_double)]

class Primaries(C.Structure):
    _fields_ = [('Red', CIExyY), ('Green', CIExyY), ('Blue', CIExyY)]

class LittleCMS:
    def __init__(self, library=None):
        candidates = [library or os.environ.get('INKPROF_LCMS2_LIBRARY')]
        if not candidates[0]:
            from PIL import _imagingcms
            candidates = [_imagingcms.__file__, ctypes.util.find_library('lcms2')]
        errors=[]
        loader=C.WinDLL if os.name=='nt' else C.CDLL
        for path in candidates:
            if not path: continue
            try:
                lib=loader(str(path))
                definitions={
                    'cmsGetEncodedCMMversion':([],C.c_uint32),
                    'cmsOpenProfileFromMem':([C.c_void_p,C.c_uint32],C.c_void_p),
                    'cmsCreate_sRGBProfile':([],C.c_void_p),
                    'cmsBuildGamma':([C.c_void_p,C.c_double],C.c_void_p),
                    'cmsFreeToneCurve':([C.c_void_p],None),
                    'cmsCreateRGBProfile':([C.POINTER(CIExyY),C.POINTER(Primaries),C.POINTER(C.c_void_p)],C.c_void_p),
                    'cmsCreateLab4Profile':([C.c_void_p],C.c_void_p),
                    'cmsSaveProfileToFile':([C.c_void_p,C.c_char_p],C.c_int),
                    'cmsCreateTransform':([C.c_void_p,C.c_uint32,C.c_void_p,C.c_uint32,C.c_uint32,C.c_uint32],C.c_void_p),
                    'cmsDoTransform':([C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint32],None),
                    'cmsDeleteTransform':([C.c_void_p],None),
                    'cmsCloseProfile':([C.c_void_p],C.c_int),
                }
                for name,(args,result) in definitions.items():
                    fn=getattr(lib,name);fn.argtypes=args;fn.restype=result
                self.lib=lib;self.path=str(path);self.version=int(lib.cmsGetEncodedCMMversion());return
            except (OSError,AttributeError) as exc: errors.append(str(exc))
        raise RuntimeError('LittleCMS C API unavailable. Set INKPROF_LCMS2_LIBRARY to a matching library. '+ '; '.join(errors))

    def save_lab_profile(self, path):
        handle=self.lib.cmsCreateLab4Profile(None)
        if not handle: raise ValueError('Cannot create Lab profile.')
        try:
            if not self.lib.cmsSaveProfileToFile(handle,os.fsencode(path)):
                raise ValueError('Cannot save Lab source profile.')
        finally: self.lib.cmsCloseProfile(handle)

    def transform(self, profile, values, direction='f', intent=1):
        if direction not in ('f','b','lab-identity'): raise ValueError('Unsupported direction.')
        if intent not in (0,1,2,3): raise ValueError('Unsupported rendering intent.')
        values=np.ascontiguousarray(values,dtype=np.float64)
        if values.ndim!=2 or values.shape[1]!=3 or not np.isfinite(values).all(): raise ValueError('Expected finite N x 3 values.')
        out=np.empty_like(values);lib=self.lib;handles=[];transform=None
        try:
            lab=lib.cmsCreateLab4Profile(None)
            if not lab: raise ValueError('Cannot create Lab profile.')
            handles.append(lab)
            if direction=='lab-identity': src=dst=lab;itype=otype=LAB_DBL
            else:
                data=Path(profile).read_bytes();buffer=C.create_string_buffer(data)
                icc=lib.cmsOpenProfileFromMem(buffer,len(data))
                if not icc: raise ValueError('LittleCMS rejected profile.')
                handles.append(icc)
                src,dst,itype,otype=(icc,lab,RGB_DBL,LAB_DBL) if direction=='f' else (lab,icc,LAB_DBL,RGB_DBL)
            # Relative colorimetric, no BPC; disable cache/optimization for diagnostic evaluation.
            transform=lib.cmsCreateTransform(src,itype,dst,otype,intent,0x0100|0x0040)
            if not transform: raise ValueError('LittleCMS could not build transform.')
            lib.cmsDoTransform(transform,values.ctypes.data,out.ctypes.data,len(values))
            if not np.isfinite(out).all(): raise ValueError('Nonfinite LittleCMS output.')
            return out
        finally:
            if transform: lib.cmsDeleteTransform(transform)
            for handle in reversed(handles): lib.cmsCloseProfile(handle)

    def photo_transform(self, profile, values, space='sRGB', intent=1, bpc=False, bits=None):
        """Actual RGB working-profile -> printer-profile CMM chain, RGB buffers.
        bits=None uses doubles; 8/16 use integer input AND output buffers.
        No printer/driver conversion is simulated after this transform.
        """
        if space not in ('sRGB', 'Adobe RGB (1998)') or intent not in (0,1) or bits not in (None,8,16):
            raise ValueError('Unsupported photographic conversion settings.')
        values=np.asarray(values,dtype=float)
        if values.ndim!=2 or values.shape[1]!=3 or not np.isfinite(values).all() or (values<0).any() or (values>1).any():
            raise ValueError('Source RGB must be finite N x 3 in [0,1].')
        lib=self.lib;handles=[];transform=None;curve=None
        try:
            if space=='sRGB': src=lib.cmsCreate_sRGBProfile()
            else:
                white=CIExyY(.3127,.3290,1)
                prim=Primaries(CIExyY(.64,.33,1),CIExyY(.21,.71,1),CIExyY(.15,.06,1))
                curve=lib.cmsBuildGamma(None,563/256)
                if not curve: raise ValueError('Cannot create Adobe RGB tone curve.')
                curves=(C.c_void_p*3)(curve,curve,curve)
                src=lib.cmsCreateRGBProfile(C.byref(white),C.byref(prim),curves)
            if not src: raise ValueError('Cannot create working RGB profile.')
            handles.append(src)
            data=Path(profile).read_bytes();buffer=C.create_string_buffer(data)
            dst=lib.cmsOpenProfileFromMem(buffer,len(data))
            if not dst: raise ValueError('LittleCMS rejected printer profile.')
            handles.append(dst)
            if bits is None:
                src_values=np.ascontiguousarray(values,dtype=np.float64);pixel_type=RGB_DBL;scale=1
            else:
                scale=2**bits-1
                src_values=np.ascontiguousarray(np.round(values*scale),dtype=np.uint8 if bits==8 else np.uint16)
                pixel_type=(4<<16)|(3<<3)|(bits//8)
            out=np.empty_like(src_values)
            flags=0x0100|0x0040|(0x2000 if bpc else 0)
            transform=lib.cmsCreateTransform(src,pixel_type,dst,pixel_type,intent,flags)
            if not transform: raise ValueError('Cannot build photographic conversion.')
            lib.cmsDoTransform(transform,src_values.ctypes.data,out.ctypes.data,len(values))
            result=out.astype(float)/scale
            if not np.isfinite(result).all(): raise ValueError('Nonfinite photographic output.')
            return np.clip(result,0,1)
        finally:
            if transform: lib.cmsDeleteTransform(transform)
            for handle in reversed(handles): lib.cmsCloseProfile(handle)
            if curve: lib.cmsFreeToneCurve(curve)
