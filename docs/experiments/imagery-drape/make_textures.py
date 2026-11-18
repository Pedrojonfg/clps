"""Experiment (D-20261118-pj-f6b3): build albedo textures from the LROC WAC south summer mosaic.

Usage, from the repo root: python docs/experiments/imagery-drape/make_textures.py <out_dir>
Writes a.png (photo where lit, transparent in shadow) and b.png (shadows filled, illumination envelope
removed). 60 km east-north square around Site01, 100 m/px, row 0 = north.
"""
import math, numpy as np, rasterio
from rasterio.windows import from_bounds
from scipy.ndimage import map_coordinates, gaussian_filter
from PIL import Image
import sys
from moonpark.horizon import polar_stereo_xy  # run from the repo root
lat,lon=-89.46316,222.51045
OUT=sys.argv[1] if len(sys.argv)>1 else "."  # directory for a.png / b.png (served to the page as ?albedo=URL)
OUT=OUT.rstrip("/")+"/"
x0,y0=polar_stereo_xy(lat,lon); L=math.radians(lon)
east=np.array([math.cos(L),-math.sin(L)]); north=np.array([math.sin(L),math.cos(L)])
R=30000; step=100.0; n=int(2*R/step)
src=rasterio.open('data/imagery/WAC_ROI_SOUTH_SUMMER_100M.TIF')
w=from_bounds(x0-R*1.5,y0-R*1.5,x0+R*1.5,y0+R*1.5,src.transform).round_offsets().round_lengths()
a=src.read(1,window=w).astype(np.float32); tr=src.window_transform(w)
e=(np.arange(n)+0.5)*step-R; nn=R-(np.arange(n)+0.5)*step  # row 0 = north
E_,N_=np.meshgrid(e,nn)
X=x0+E_*east[0]+N_*north[0]; Y=y0+E_*east[1]+N_*north[1]
col=(X-tr.c)/tr.a-0.5; row=(tr.f-Y)/(-tr.e)-0.5 if tr.e<0 else (Y-tr.f)/tr.e-0.5
img=map_coordinates(a,[row,col],order=1,mode="nearest")
lit=img>=22
print("lit frac",lit.mean())
# normalized-convolution fill of shadows with local lit mean
def fill(v,m,s):
    num=gaussian_filter(np.where(m,v,0),s); den=gaussian_filter(m.astype(float),s)
    return np.where(den>1e-3,num/np.maximum(den,1e-3),np.nan)
def save(name,v,alpha):
    rgba=np.dstack([v,v,v,alpha]).astype(np.uint8)
    Image.fromarray(rgba,"RGBA").save(OUT+name)
# option a: photo where lit, invalid elsewhere (client mixes procedural)
save("a.png",np.clip(img,0,255),np.where(lit,255,0))
# option b (approximation): shadows inpainted, large-scale illumination removed
f=fill(img,lit,6.0)
f=np.where(np.isnan(f),np.nanmedian(f),f)
f=np.where(lit,img,f)
low=gaussian_filter(f,25.0)           # ~2.5 km illumination envelope
alb=f/np.maximum(low,8.0)
alb=np.clip(alb/np.percentile(alb,99.5),0,1)*0.75
save("b.png",np.clip(alb*255,0,255),np.full_like(alb,255))
print("done")
