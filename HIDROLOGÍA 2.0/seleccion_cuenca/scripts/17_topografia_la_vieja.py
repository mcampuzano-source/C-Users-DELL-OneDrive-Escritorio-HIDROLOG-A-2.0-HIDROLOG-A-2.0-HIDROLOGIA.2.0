"""Descarga pública Copernicus GLO-30 y recorte al polígono CAMELS."""
from pathlib import Path
import json, hashlib, urllib.request
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.enums import Resampling
from shapely.geometry import shape

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'la_vieja'/'topografia'
OUT.mkdir(exist_ok=True)
name='Copernicus_DSM_COG_10_N04_00_W076_00_DEM'
url=f'https://copernicus-dem-30m.s3.amazonaws.com/{name}/{name}.tif'
tile=OUT/(name+'.tif')
if not tile.exists():
    urllib.request.urlretrieve(url,tile)
features=json.loads((ROOT/'resultados'/'ocho_cuencas_wgs84.geojson').read_text(encoding='utf-8'))['features']
feature=next(f for f in features if f['properties']['gauge_id']==26127040)
poly=shape(feature['geometry'])
(OUT/'cuenca_la_vieja.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[feature]},ensure_ascii=False),encoding='utf-8')
with rasterio.open(tile) as src:
    assert src.crs.to_epsg()==4326
    west,south,east,north=poly.bounds
    assert src.bounds.left<=west and src.bounds.right>=east and src.bounds.bottom<=south and src.bounds.top>=north
    cropped,transform=mask(src,[feature['geometry']],crop=True,nodata=-9999,filled=True)
    profile=src.profile.copy()
    profile.update(height=cropped.shape[1],width=cropped.shape[2],transform=transform,nodata=-9999,compress='deflate')
    with rasterio.open(OUT/'dem_la_vieja_30m.tif','w',**profile) as dst:
        dst.write(cropped)
with rasterio.open(OUT/'dem_la_vieja_30m.tif') as src:
    # Submuestreo por promedio SOLO para dibujar; conservar el GeoTIFF a resolución nativa.
    h=350; w=round(src.width*h/src.height)
    small=src.read(1,out_shape=(h,w),resampling=Resampling.average,masked=True)
    affine=src.transform*src.transform.scale(src.width/w,src.height/h)
    x=affine.c+(np.arange(w)+.5)*affine.a
    y=affine.f+(np.arange(h)+.5)*affine.e
    np.savez_compressed(OUT/'relieve_visualizacion.npz',z=small.filled(np.nan),x=x,y=y)
valid=cropped[cropped!=-9999]
notice='produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved'
meta={'producto':'Copernicus DEM GLO-30 Public COG','tipo':'DSM: incluye vegetación y construcciones; no es un DTM de terreno desnudo','url':url,'tile':name,'sha256':hashlib.sha256(tile.read_bytes()).hexdigest(),'crs_horizontal':'EPSG:4326','referencia_vertical':'EGM2008; metros según documentación Copernicus','resolucion_grados':abs(transform.a),'resolucion_nominal':'1 segundo de arco, aproximadamente 30 m','min_m':float(valid.min()),'max_m':float(valid.max()),'media_pixeles_m':float(valid.mean()),'pixeles_validos':int(valid.size),'estadistica':'Resumen exploratorio de centros de píxel; no ponderación geodésica por área','adquisicion_general':'TanDEM-X 2011–2015 con rellenos de otras fuentes; no topografía histórica 1981–2022','atribucion':notice,'documentacion':'https://copernicus-dem-30m.s3.amazonaws.com/readme.html','licencia_fuente':'https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM'}
(OUT/'metadatos_dem.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'ATRIBUCION.txt').write_text(notice,encoding='utf-8')
print(json.dumps(meta,ensure_ascii=False,indent=2))
