"""Public NOAA global monthly fields. Small cached chunks avoid interrupted transfers."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
import json, hashlib, shutil, tempfile
import requests, xarray as xr, netCDF4
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'datos/clima_global_5_1'
CACHE=OUT/'fragmentos'; CACHE.mkdir(parents=True,exist_ok=True)
FIELDS={'sst':('noaa.ersst.v5/sst.mnmean.nc','sst',None),'slp':('ncep.reanalysis.derived/surface/slp.mon.mean.nc','slp',None),'z500':('ncep.reanalysis.derived/pressure/hgt.mon.mean.nc','hgt',500),'psfc':('ncep.reanalysis.derived/surface/pres.sfc.mon.mean.nc','pres',None)}
def request(name,start,end):
 path,var,level=FIELDS[name]
 params={'var':var,'north':90,'south':-90,'west':0,'east':360,'horizStride':1,'time_start':f'{start}-01-01T00:00:00Z','time_end':f'{end}-12-01T00:00:00Z','timeStride':1,'accept':'netcdf4'}
 if level is not None:params['vertCoord']=level
 return path,params
def fetch(task):
 name,start,end=task;target=CACHE/f'{name}_{start}_{end}.nc';path,params=request(*task)
 if target.exists():return {'field':name,'file':str(target),'cached':True}
 errors=[]
 for host in ['www.psl.noaa.gov','psl.noaa.gov','www.psl.noaa.gov']:
  try:
   r=requests.get(f'https://{host}/thredds/ncss/grid/Datasets/{path}',params=params,timeout=(12,45));r.raise_for_status()
   assert r.content[:3] in (b'CDF',b'\x89HD'), 'Not a NetCDF response'
   target.write_bytes(r.content)
   info={'field':name,'file':str(target),'url':r.url,'bytes':len(r.content),'sha256':hashlib.sha256(r.content).hexdigest(),'retrieved_at':datetime.now(ZoneInfo('America/Bogota')).isoformat()}
   target.with_suffix('.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
   print(name,start,end,'OK',len(r.content),flush=True);return info
  except Exception as e:
   errors.append(type(e).__name__+': '+str(e)[:180]);print(name,start,end,errors[-1],flush=True)
 return {'field':name,'status':'pending','errors':errors}
def load(path):
 with tempfile.TemporaryDirectory(prefix='hydro_nc_') as tmp:
  f=Path(tmp)/'input.nc';shutil.copyfile(path,f)
  with xr.open_dataset(f,engine='netcdf4') as ds:return ds.load()
def normalize(ds,name):
 _,var,level=FIELDS[name]
 ds=ds.sel(time=slice('1981-01-01','2022-12-01'))
 if 'level' in ds[var].dims:ds=ds.sel(level=level)
 assert ds.sizes['time']==504
 months=ds.time.dt.strftime('%Y-%m').values.tolist();assert len(set(months))==504 and months[0]=='1981-01' and months[-1]=='2022-12'
 target=OUT/f'{name}_1981_2022.nc'
 with tempfile.TemporaryDirectory(prefix='hydro_nc_') as tmp:
  f=Path(tmp)/'out.nc';ds.to_netcdf(f,engine='netcdf4',encoding={var:{'zlib':True,'complevel':4}});shutil.copyfile(f,target)
 return {'field':name,'status':'downloaded','months':504,'path':str(target.relative_to(ROOT)),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'shape':list(ds[var].shape),'units':ds[var].attrs.get('units'),'source':FIELDS[name][0],'request':request(name,1981,2022)[1],'retrieved_at':datetime.now(ZoneInfo('America/Bogota')).isoformat()}
if __name__=='__main__':
 result=[];tasks=[];ready={}
 for name in FIELDS:
  p=OUT/f'{name}_1981_2022.nc'
  if p.exists():
   try:ready[name]=load(p);continue
   except Exception:pass
  tasks.extend((name,y,min(y+4,2022)) for y in range(1981,2023,5))
 with ThreadPoolExecutor(max_workers=6) as pool:logs=list(pool.map(fetch,tasks))
 (OUT/'journal_requetes.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
 for name in FIELDS:
  try:
   if name in ready:ds=ready[name]
   else:
    chunks=[load(CACHE/f'{name}_{y}_{min(y+4,2022)}.nc') for y in range(1981,2023,5)]
    ds=xr.concat(chunks,dim='time');ds=ds.sortby('time');_,unique=__import__('numpy').unique(ds.time.values,return_index=True);ds=ds.isel(time=unique)
   result.append(normalize(ds,name));print(name,'504 months validated',flush=True)
  except Exception as e:result.append({'field':name,'status':'pending','error':str(e)[:220]})
 (OUT/'estado_descargas.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
 print(json.dumps(result,indent=2),flush=True)
