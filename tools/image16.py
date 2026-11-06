# Copyright (c) 2026 Christer Törnkvist <christer@borgasundsfotografiska.se>
# SPDX-License-Identifier: GPL-3.0-or-later
"""Lossless uint16 raster storage, PNG/TIFF I/O and LittleCMS transforms.

Pillow's multichannel 8-bit decoder is deliberately bypassed for 16-bit data.
"""
import ctypes as C
from pathlib import Path
import struct
import sys
import zlib
import numpy as np
from PIL import Image

if not getattr(sys,'frozen',False):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'analysis'))
from lcms_float import LittleCMS


class Image16:
    bits=16

    def __init__(self, array, mode, info=None):
        values=np.asarray(array)
        if values.dtype.kind!='u' or values.dtype.itemsize!=2:
            raise ValueError('Endast osignerade 16-bitars heltal stöds.')
        if values.ndim==2: values=values[:,:,None]
        if values.ndim!=3 or values.shape[2]!=len(self.bands(mode)):
            raise ValueError('Bildens kanaler stämmer inte med färgrymden.')
        self.array=np.ascontiguousarray(values,dtype=np.uint16)
        self.mode=mode; self.info=dict(info or {})

    @staticmethod
    def bands(mode): return {'RGB':('R','G','B'),'RGBA':('R','G','B','A'),'CMYK':('C','M','Y','K'),'L':('L',),'LA':('L','A'),'LAB':('L','a','b')}[mode]
    @property
    def width(self): return self.array.shape[1]
    @property
    def height(self): return self.array.shape[0]
    @property
    def size(self): return self.width,self.height
    def getbands(self): return self.bands(self.mode)
    def __array__(self,dtype=None,copy=None):
        result=np.asarray(self.array,dtype=dtype)
        return result.copy() if copy else result
    def copy(self): return Image16(self.array.copy(),self.mode,self.info)
    def crop(self,box):
        x,y,r,b=box;return Image16(self.array[y:b,x:r].copy(),self.mode,self.info)
    def getpixel(self,position):
        x,y=position;v=self.array[y,x]
        return int(v[0]) if len(v)==1 else tuple(map(int,v))
    def getchannel(self,channel):
        return Image16(self.array[:,:,self.getbands().index(channel)],'L')
    def convert(self,mode):
        if mode==self.mode: return self.copy()
        if (self.mode,mode) in (('RGBA','RGB'),('LA','L')):
            return Image16(self.array[:,:,:-1],mode,self.info)
        raise ValueError('16-bitars färgkonvertering kräver ICC-profiler.')
    def putalpha(self,alpha):
        if self.mode not in ('RGB','L'): raise ValueError('Alfa stöds endast för RGB och gråskala.')
        values=alpha.array if isinstance(alpha,Image16) else np.full((self.height,self.width,1),alpha,dtype=np.uint16)
        self.array=np.concatenate((self.array,values),axis=2);self.mode+='A'
    def tobytes(self): return self.array.tobytes()
    def thumbnail(self,size,resample=None):
        ratio=min(size[0]/self.width,size[1]/self.height,1)
        if ratio==1: return
        dimensions=(max(1,round(self.width*ratio)),max(1,round(self.height*ratio)))
        self.array=np.stack([np.clip(np.rint(np.asarray(Image.fromarray(self.array[:,:,i].astype(np.float32)).resize(dimensions,Image.Resampling.LANCZOS))),0,65535).astype(np.uint16) for i in range(self.array.shape[2])],axis=2)
    def save(self,path,format=None,**options):
        fmt=(format or {'.png':'PNG','.tif':'TIFF','.tiff':'TIFF'}.get(Path(path).suffix.lower()))
        if fmt not in ('PNG','TIFF'):
            raise ValueError('16-bitarsbilder måste sparas som TIFF eller PNG. JPEG stöder bara 8 bitar.')
        icc=options.get('icc_profile',self.info.get('icc_profile'))
        dpi=options.get('dpi',self.info.get('dpi'))
        if fmt=='TIFF':
            import tifffile
            if self.mode=='LAB': raise ValueError('16-bitars Lab-export stöds inte. Välj en RGB- eller CMYK-profil.')
            alpha=self.mode in ('RGBA','LA')
            data=self.array[:,:,0] if self.mode=='L' else self.array
            tifffile.imwrite(path,data,photometric=('separated' if self.mode=='CMYK' else 'rgb' if self.mode.startswith('RGB') else 'minisblack'),
                extrasamples=('unassalpha',) if alpha else None,compression='deflate',metadata=None,
                iccprofile=icc,resolution=dpi,resolutionunit='INCH' if dpi else None)
        else:
            if self.mode not in ('RGB','RGBA','L','LA'): raise ValueError('PNG stöder inte CMYK eller Lab. Välj TIFF.')
            import imagecodecs
            data=imagecodecs.png_encode(self.array[:,:,0] if self.mode=='L' else self.array,level=options.get('compress_level',6))
            def chunk(name,payload):
                return struct.pack('>I',len(payload))+name+payload+struct.pack('>I',zlib.crc32(name+payload)&0xffffffff)
            extra=chunk(b'iCCP',b'ICC Profile\0\0'+zlib.compress(icc)) if icc else b''
            if dpi: extra+=chunk(b'pHYs',struct.pack('>IIB',round(dpi[0]/.0254),round(dpi[1]/.0254),1))
            # IHDR is always the first PNG chunk (25 bytes including framing).
            Path(path).write_bytes(data[:33]+extra+data[33:])


def oriented(array,orientation):
    if orientation==2:return array[:,::-1]
    if orientation==3:return array[::-1,::-1]
    if orientation==4:return array[::-1]
    if orientation==5:return array.transpose(1,0,2)
    if orientation==6:return np.rot90(array,3)
    if orientation==7:return array.transpose(1,0,2)[::-1,::-1]
    if orientation==8:return np.rot90(array,1)
    return array


def read_image16(path,opened):
    info=dict(opened.info)
    if opened.format=='TIFF':
        import tifffile
        with tifffile.TiffFile(path) as file:
            if len(file.pages)!=1: raise ValueError('Bilder med flera sidor eller bildrutor stöds inte.')
            page=file.pages[0]
            sample_bits=page.bitspersample
            sample_bits=(sample_bits,) if isinstance(sample_bits,int) else sample_bits
            if page.dtype.kind!='u' or page.dtype.itemsize!=2 or any(b!=16 for b in sample_bits):
                raise ValueError('Endast 8 eller osignerade 16 bitar per kanal stöds; inte 32 bitar eller flyttal.')
            values=page.asarray()
            if int(page.planarconfig)==2: values=np.moveaxis(values,0,-1)
            if values.ndim==2: values=values[:,:,None]
            photo=int(page.photometric);channels=values.shape[-1]
            if photo==2 and channels in (3,4): mode='RGB' if channels==3 else 'RGBA'
            elif photo in (0,1) and channels in (1,2):
                mode='L' if channels==1 else 'LA'
            elif photo==5 and channels==4: mode='CMYK'
            else: raise ValueError('16-bitars TIFF stöder RGB, CMYK eller gråskala. Konvertera andra färgmodeller först.')
            if mode in ('RGBA','LA'):
                extras=tuple(map(int,page.extrasamples))
                if extras==(1,):
                    values=values.copy()
                    for start in range(0,values.shape[0],64):
                        block=values[start:start+64]
                        alpha=block[:,:,-1:].astype(np.float64)
                        straight=np.divide(block[:,:,:-1].astype(np.float64)*65535,alpha,out=np.zeros_like(block[:,:,:-1],dtype=float),where=alpha>0)
                        block[:,:,:-1]=np.clip(np.rint(straight),0,65535).astype(np.uint16)
                elif extras!=(2,): raise ValueError('TIFF-bildens extra kanaler är inte entydigt markerade som alfa.')
            if photo==0:
                values=values.copy();values[:,:,0]=65535-values[:,:,0]
            if 34675 in page.tags: info['icc_profile']=bytes(page.tags[34675].value)
            def resolution(tag):
                value=page.tags[tag].value
                return value[0]/value[1] if isinstance(value,tuple) else float(value)
            if 282 in page.tags and 283 in page.tags:
                unit=int(page.tags[296].value) if 296 in page.tags else 2
                if unit in (2,3): info['dpi']=tuple(resolution(t)*(2.54 if unit==3 else 1) for t in (282,283))
            orientation=int(page.tags[274].value) if 274 in page.tags else 1
    else:
        import imagecodecs
        values=imagecodecs.png_decode(Path(path).read_bytes())
        channels=1 if values.ndim==2 else values.shape[-1]
        mode={1:'L',2:'LA',3:'RGB',4:'RGBA'}[channels]
        if values.ndim==2:values=values[:,:,None]
        orientation=int(opened.getexif().get(274,1))
    if orientation in (5,6,7,8) and info.get('dpi'):
        info['dpi']=tuple(reversed(info['dpi']))
    return Image16(oriented(values,orientation),mode,info)


def transform16(image,source,target,mode,intent,bpc):
    from icc_processing import profile_mode
    if source is None or profile_mode(source)!=image.mode:
        raise ValueError('Källprofilens färgrymd motsvarar inte bildens kanaler.')
    if profile_mode(target)!=mode: raise ValueError('Målprofilens färgrymd motsvarar inte bildens kanaler.')
    channels={'RGB':3,'CMYK':4,'L':1,'LAB':3}
    spaces={'RGB':4,'CMYK':6,'L':3,'LAB':10}
    src_values=np.ascontiguousarray(image.array,dtype=np.uint16)
    output=np.empty((image.height,image.width,channels[mode]),dtype=np.uint16)
    cms=LittleCMS();lib=cms.lib;handles=[];transform=None;buffers=[]
    try:
        for profile in (source,target):
            data=profile.tobytes();buffer=C.create_string_buffer(data);buffers.append(buffer)
            handle=lib.cmsOpenProfileFromMem(buffer,len(data))
            if not handle: raise ValueError('ICC-profilen kunde inte öppnas.')
            handles.append(handle)
        itype=(spaces[image.mode]<<16)|(channels[image.mode]<<3)|2
        otype=(spaces[mode]<<16)|(channels[mode]<<3)|2
        transform=lib.cmsCreateTransform(handles[0],itype,handles[1],otype,intent,0x0100|0x0040|(0x2000 if bpc else 0))
        if not transform: raise ValueError('16-bitars ICC-konverteringen kunde inte skapas.')
        # Chunk the transform to keep the C API's uint32 pixel count bounded.
        src=src_values.reshape(-1,channels[image.mode]);dst=output.reshape(-1,channels[mode])
        for start in range(0,len(src),1048576):
            end=min(start+1048576,len(src));lib.cmsDoTransform(transform,src[start:end].ctypes.data,dst[start:end].ctypes.data,end-start)
        return Image16(output,mode,{'icc_profile':target.tobytes()})
    finally:
        if transform:lib.cmsDeleteTransform(transform)
        for handle in reversed(handles):lib.cmsCloseProfile(handle)
