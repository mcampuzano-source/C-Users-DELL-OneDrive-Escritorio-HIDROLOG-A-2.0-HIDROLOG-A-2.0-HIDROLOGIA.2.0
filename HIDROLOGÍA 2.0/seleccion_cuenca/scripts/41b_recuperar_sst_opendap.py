"""Respaldo ERSSTv5 por OPeNDAP cuando NCSS no puede crear recortes.

Lee una respuesta DAP2 Grid SST con sus tres coordenadas. Valida cantidades,
dimensiones, coordenadas, fechas y tamaño de la respuesta antes de guardarla.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import importlib.util
import re
import struct
import json
import hashlib
import tempfile
import shutil
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
import numpy as np
import pandas as pd
import xarray as xr

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'datos/clima_global_5_1'
CACHE=OUT/'fragmentos'
URL='https://www.psl.noaa.gov/thredds/dodsC/Datasets/noaa.ersst.v5/sst.mnmean.nc'

def fetch(year):
    end=min(year+4,2022)
    target=CACHE/f'sst_{year}_{end}.nc'
    if target.exists():return None
    start=(year-1854)*12
    stop=(end-1854)*12+11
    url=URL+f'.dods?sst[{start}:1:{stop}][0:1:88][0:1:179]'
    r=requests.get(url,timeout=(12,60));r.raise_for_status()
    header,data=r.content.split(b'Data:\n',1)
    text=header.decode()
    dims=re.search(r'Float32 sst\[time = (\d+)\]\[lat = (\d+)\]\[lon = (\d+)\]',text)
    assert dims
    shape=tuple(map(int,dims.groups()))
    assert shape==((end-year+1)*12,89,180),shape
    offset=0
    def array(dtype,expected):
        nonlocal offset
        n,n2=struct.unpack_from('>II',data,offset);offset+=8
        assert n==n2==expected
        a=np.frombuffer(data,dtype=dtype,count=n,offset=offset).astype(float)
        offset+=n*np.dtype(dtype).itemsize
        return a
    values=array('>f4',int(np.prod(shape))).reshape(shape)
    times=array('>f8',shape[0]);lat=array('>f4',89);lon=array('>f4',180)
    assert offset==len(data)
    assert np.allclose(lat,np.arange(88,-90,-2))
    assert np.allclose(lon,np.arange(0,360,2))
    dates=pd.Timestamp('1800-01-01')+pd.to_timedelta(times,unit='D')
    assert dates[0]==pd.Timestamp(f'{year}-01-01')
    assert dates[-1]==pd.Timestamp(f'{end}-12-01')
    values[values < -1e30]=np.nan
    assert np.nanmin(values)>=-2 and np.nanmax(values)<50
    info={'url':url,'retrieved_at':datetime.now(ZoneInfo('America/Bogota')).isoformat(),
          'protocol':'DAP2 Grid, FLOAT32 SST y coordenadas FLOAT64/FLOAT32',
          'source_sha256_dods':hashlib.sha256(r.content).hexdigest(),'shape':shape}
    print('SST OPeNDAP',year,end,'recibido',flush=True)
    return target,values,dates,lat,lon,info

if __name__=='__main__':
    # Avoid concurrent HDF5/netCDF calls: HTTP in parallel, all file writes serial.
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(fetch,range(1981,2023,5)))
    for item in filter(None,results):
        target,values,dates,lat,lon,info=item
        ds=xr.Dataset({'sst':(('time','lat','lon'),values.astype('float32'))},coords={'time':dates,'lat':lat,'lon':lon})
        ds.sst.attrs.update(units='degC',long_name='Monthly mean sea surface temperature',dataset='NOAA ERSST V5')
        ds.attrs.update(dataset_title='NOAA ERSST V5',source=URL)
        with tempfile.TemporaryDirectory(prefix='hydro_sst_') as tmp:
            f=Path(tmp)/'sst.nc';ds.to_netcdf(f,engine='netcdf4',encoding={'sst':{'zlib':True,'complevel':4}});shutil.copyfile(f,target)
        info['sha256']=hashlib.sha256(target.read_bytes()).hexdigest()
        target.with_suffix('.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
