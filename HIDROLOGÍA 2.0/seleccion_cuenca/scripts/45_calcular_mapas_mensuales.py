"""Correlaciones interanuales por mes calendario y celda (apartado 5.2).

Referencias: 285 fechas completas de cuenca, climatologías fijas 1998-2022.
Rezago positivo: campo global antecede a la respuesta de cuenca.
"""
from pathlib import Path
import importlib.util
import json
import hashlib
import tempfile
import shutil
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'la_vieja/documentos'
OUT=DOCS/'apartado_5_2'
OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('fields51',Path(__file__).with_name('41_descargar_campos_globales.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
RAW=ROOT/'datos/clima_global_5_1'
MONTHS=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
RESPONSE={'CHIRPS':('P_CHIRPS_mm','Precipitación CHIRPS','mm/mes'),
          'Q':('Q_m3_s','Caudal Cartago','m³/s'),
          'IMERG':('P_IMERG_poligono_mm','Precipitación IMERG','mm/mes')}
FIELD={'sst':('sst','SST ERSSTv5','°C'), 'slp':('slp','SLP NCEP/NCAR R1','hPa'),
       'z500':('hgt','Z500 NCEP/NCAR R1','m')}
input_path=DOCS/'imerg_poligono/series_alineadas.csv'
df=pd.read_csv(input_path,parse_dates=['mes']).set_index('mes')
common=df.loc['1998-01-01':'2022-12-01',[v[0] for v in RESPONSE.values()]].dropna()
assert len(common)==285
anom=common-common.groupby(common.index.month).transform('mean')
anom.to_csv(OUT/'anomalias_cuenca.csv',index_label='mes_respuesta')

def correlation(x,y):
    """Pearson vectorizado, con la misma máscara para ambas variables."""
    y=np.broadcast_to(np.asarray(y)[:,None],x.shape)
    valid=np.isfinite(x)&np.isfinite(y)
    n=valid.sum(axis=0)
    den=np.maximum(n,1)
    xx=np.where(valid,x,0);yy=np.where(valid,y,0)
    mx=xx.sum(axis=0)/den;my=yy.sum(axis=0)/den
    dx=np.where(valid,x-mx,0);dy=np.where(valid,y-my,0)
    vx=(dx*dx).sum(axis=0);vy=(dy*dy).sum(axis=0)
    r=np.divide((dx*dy).sum(axis=0),np.sqrt(vx*vy),out=np.full(x.shape[1],np.nan),where=(vx>1e-16)&(vy>1e-16))
    return np.clip(r,-1,1),n

def spearman(x,y):
    yy=np.broadcast_to(np.asarray(y)[:,None],x.shape).copy()
    valid=np.isfinite(x)&np.isfinite(yy)
    xx=np.where(valid,x,np.nan);yy[~valid]=np.nan
    rx=pd.DataFrame(xx).rank(axis=0,method='average',na_option='keep').to_numpy()
    ry=pd.DataFrame(yy).rank(axis=0,method='average',na_option='keep').to_numpy()
    # Pearson of ranks, pairwise and tie-aware.
    n=valid.sum(axis=0);den=np.maximum(n,1)
    dx=np.where(valid,rx-np.nansum(rx,axis=0)/den,0)
    dy=np.where(valid,ry-np.nansum(ry,axis=0)/den,0)
    div=np.sqrt((dx*dx).sum(axis=0)*(dy*dy).sum(axis=0))
    return np.divide((dx*dy).sum(axis=0),div,out=np.full(x.shape[1],np.nan),where=div>1e-16)

# Meaningful checks: ties, pairwise missingness, monotonic nonlinearity.
t=np.arange(24,dtype=float)
assert abs(spearman((t*t)[:,None],t)[0]-1)<1e-12
test=np.array([[1,1],[2,np.nan],[2,3],[4,4],[5,5]],float);target=np.array([1,2,3,4,5],float)
sr=spearman(test,target)
for j in range(2):
    ok=np.isfinite(test[:,j]);expected=np.corrcoef(pd.Series(test[ok,j]).rank(),pd.Series(target[ok]).rank())[0,1]
    assert abs(sr[j]-expected)<1e-12

fields={};attrs={}
for key,(var,label,unit) in FIELD.items():
    ds=mod.load(RAW/f'{key}_1981_2022.nc')
    da=ds[var].squeeze(drop=True).reset_coords(drop=True).astype('float64')
    if key=='slp' and str(da.attrs.get('units','')).lower()=='pa':da=da/100
    da=da.assign_coords(lon=((da.lon+180)%360)-180).sortby('lon').sortby('lat')
    if key=='z500':
        ps=mod.load(RAW/'psfc_1981_2022.nc')['pres'].squeeze(drop=True).reset_coords(drop=True)
        if str(ps.attrs.get('units','')).lower()=='pa':ps=ps/100
        ps=ps.assign_coords(lon=((ps.lon+180)%360)-180).sortby('lon').sortby('lat')
        da=da.where(ps>=500)
    clim=da.sel(time=common.index).groupby('time.month').mean('time',skipna=True)
    fields[key]=(da.groupby('time.month')-clim).transpose('time','lat','lon')
    attrs[key]=dict(label=label,units=unit,sha256=hashlib.sha256((RAW/f'{key}_1981_2022.nc').read_bytes()).hexdigest())

coast=json.loads((DOCS/'apartado_5_1/ne_110m_coastline.geojson').read_bytes())
coast_lines=[]
for f in coast['features']:
    parts=f['geometry']['coordinates']
    if f['geometry']['type']=='LineString':parts=[parts]
    for part in parts:
        a=np.asarray(part,dtype=float);a[np.abs(np.diff(a[:,0],prepend=a[0,0]))>180]=np.nan;coast_lines.append(a)

def panels(ds,response,field,lag,method):
    name=f'{response}_{field}_l{lag}_{method}'
    cached_pdf=OUT/(name+'.pdf');cached_png=OUT/(name+'.png')
    if cached_pdf.exists() and cached_png.exists() and cached_pdf.stat().st_size>1000 and cached_png.stat().st_size>1000:return name
    fig,axes=plt.subplots(4,3,figsize=(12.8,9),sharex=True,sharey=True)
    fig.subplots_adjust(left=.045,right=.975,top=.90,bottom=.12,wspace=.055,hspace=.25)
    for m,ax in enumerate(axes.flat,1):
        a=ds[method].sel(month=m);n=ds.n_pairs.sel(month=m).values
        im=ax.pcolormesh(ds.lon,ds.lat,a.values,shading='auto',cmap='RdBu_r',vmin=-1,vmax=1,rasterized=True)
        ax.set_facecolor('#eeeeee')
        ax.add_collection(LineCollection(coast_lines,linewidths=.35,colors='#404040'))
        ax.plot(-75.7,4.45,'*',color='black',ms=4)
        ok=np.isfinite(a.values);counts=n[ok]
        text='sin pares suficientes' if not len(counts) else f'n={int(counts.min())}' if counts.min()==counts.max() else f'n={int(counts.min())}–{int(counts.max())}'
        ax.set_title(f'{MONTHS[m-1]} · {text}',fontsize=9,pad=3)
        ax.set(xlim=(-180,180),ylim=(-90,90),xticks=[-180,-90,0,90,180],yticks=[-90,-45,0,45,90])
        ax.tick_params(labelsize=7,length=2);ax.grid(alpha=.12)
        if m>9:ax.set_xlabel('Longitud (°)',fontsize=8)
        if (m-1)%3==0:ax.set_ylabel('Latitud (°)',fontsize=8)
    stat='Pearson r' if method=='pearson' else 'Spearman ρ'
    fig.suptitle(f'{RESPONSE[response][1]} frente a {FIELD[field][1]}\n{stat} por mes calendario de la respuesta · ℓ={lag} mes(es)',fontsize=13,y=.98)
    cb=fig.colorbar(im,cax=fig.add_axes([.32,.070,.36,.014]),orientation='horizontal',ticks=[-1,-.5,0,.5,1])
    cb.ax.tick_params(labelsize=8);cb.set_label('Coeficiente adimensional · misma escala en todos los paneles',fontsize=8)
    fig.text(.045,.043,'Respuesta: 1998–2022; anomalías por mes calendario. ℓ>0: campo climático anterior a la respuesta. Gris: faltantes o n<20.',fontsize=7)
    name=f'{response}_{field}_l{lag}_{method}'
    fig.savefig(OUT/(name+'.png'),dpi=155)
    fig.savefig(OUT/(name+'.pdf'));plt.close(fig)
    return name

records=[];region_records=[];combos=[];payload={};validation=[];full_maps={}
REGIONS={'Niño 3.4':(-5,5,-170,-120),'Atlántico tropical norte':(5,25,-55,-15),'Caribe':(10,20,-85,-60)}
for response,(column,label,unit) in RESPONSE.items():
    for field in FIELD:
        for lag in ([0,1] if response=='Q' else [0]):
            da=fields[field]
            climate_dates=common.index-pd.DateOffset(months=lag)
            assert (climate_dates<=common.index).all()
            if lag==1:assert climate_dates[0]==pd.Timestamp('1997-12-01')
            x=da.sel(time=climate_dates).values.reshape(285,-1)
            y=anom[column].values
            rr=[];ss=[];nn=[]
            for month in range(1,13):
                rows=common.index.month==month
                r,n=correlation(x[rows],y[rows]);rho=spearman(x[rows],y[rows])
                mask=(n>=20)&np.isfinite(r)&np.isfinite(rho)
                r=np.where(mask,r,np.nan);rho=np.where(mask,rho,np.nan)
                rr.append(r.reshape(da.sizes['lat'],da.sizes['lon']))
                ss.append(rho.reshape(da.sizes['lat'],da.sizes['lon']))
                nn.append(n.reshape(da.sizes['lat'],da.sizes['lon']))
                weights=np.broadcast_to(np.cos(np.deg2rad(da.lat.values))[:,None],rr[-1].shape)
                good=np.isfinite(rr[-1]);w=weights[good]
                delta=np.abs(rr[-1][good]-ss[-1][good])
                strong=good&((np.abs(rr[-1])>=.2)|(np.abs(ss[-1])>=.2))
                records.append(dict(response=response,field=field,lag_months=lag,month=month,
                                    n_response=int(rows.sum()),n_min=int(n[mask].min()),n_max=int(n[mask].max()),
                                    valid_cells=int(mask.sum()),mean_abs_difference_weighted=float(np.average(delta,weights=w)),
                                    sign_disagreement_abs_02=float(np.average((np.sign(rr[-1][strong])!=np.sign(ss[-1][strong])).astype(float),weights=weights[strong]))))
                # Direct verification at a deterministic representative cell.
                j=np.flatnonzero(mask)[len(np.flatnonzero(mask))//2]
                xx=x[rows,j];yy=y[rows];ok=np.isfinite(xx)&np.isfinite(yy)
                expected=np.corrcoef(xx[ok],yy[ok])[0,1]
                assert abs(r[j]-expected)<1e-11
                expected_rho=np.corrcoef(pd.Series(xx[ok]).rank(),pd.Series(yy[ok]).rank())[0,1]
                assert abs(rho[j]-expected_rho)<1e-11
                validation.append(dict(response=response,field=field,lag=lag,month=month,pearson_error=float(abs(r[j]-expected)),spearman_error=float(abs(rho[j]-expected_rho))))
            ds=xr.Dataset(dict(pearson=(('month','lat','lon'),np.array(rr)),spearman=(('month','lat','lon'),np.array(ss)),
                               n_pairs=(('month','lat','lon'),np.array(nn,dtype='int16'))),
                          coords=dict(month=np.arange(1,13),lat=da.lat,lon=da.lon))
            ds.attrs.update(response=label,field=FIELD[field][1],lag_months=lag,lag_convention='campo(t-lag) frente a respuesta(t)',
                            reference='1998-2022: mismas 285 fechas completas de cuenca',minimum_pairs=20,
                            source_sha256=attrs[field]['sha256'],response_sha256=hashlib.sha256(input_path.read_bytes()).hexdigest(),
                            detrended='no',meaning='correlación temporal entre años del mismo mes, por celda')
            for v in ('pearson','spearman'):ds[v].attrs['units']='1'
            key=f'{response}_{field}_l{lag}'
            full_maps[key]=ds
            with tempfile.TemporaryDirectory(prefix='hydro_maps_') as tmp:
                temp=Path(tmp)/'maps.nc';ds.to_netcdf(temp,engine='netcdf4',encoding={v:{'zlib':True,'complevel':4} for v in ('pearson','spearman','n_pairs')});shutil.copyfile(temp,OUT/(key+'.nc'))
            figures=[panels(ds,response,field,lag,method) for method in ('pearson','spearman')]
            combos.append(dict(key=key,response=response,field=field,lag=lag,figures=figures))
            enc=lambda a:np.where(np.isfinite(a),np.rint(np.nan_to_num(a)*1000),-32768).astype('int16').tolist()
            payload[key]=dict(response=response,field=field,lag=lag,lat=da.lat.values.tolist(),lon=da.lon.values.tolist(),
                              r=enc(np.array(rr)),rho=enc(np.array(ss)),n=np.array(nn).tolist())
            # Region indices are predefined SST area means, not a selection of maximum map cells.
            if field=='sst':
                for region,(south,north,west,east) in REGIONS.items():
                    sub=da.sel(lat=slice(south,north),lon=slice(west,east))
                    index=sub.weighted(np.cos(np.deg2rad(sub.lat))).mean(('lat','lon')).sel(time=climate_dates).values
                    for month in range(1,13):
                        rows=common.index.month==month
                        r,n=correlation(index[rows,None],y[rows]);rho=spearman(index[rows,None],y[rows])
                        region_records.append(dict(response=response,region=region,lag=lag,month=month,n=int(n[0]),pearson=float(r[0]),spearman=float(rho[0])))
            print(key,'12 mapas por estadístico calculados',flush=True)

pd.DataFrame(records).to_csv(OUT/'diagnostico_mapas.csv',index=False)
pd.DataFrame(region_records).to_csv(OUT/'indices_sst_regionales.csv',index=False)
(OUT/'mapas_interactivos.json').write_text(json.dumps(payload,separators=(',',':'),allow_nan=False),encoding='utf-8')
(OUT/'verificacion.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
# Compare source patterns using identical spatial weights, not a significance test.
comparisons=[]
for field in FIELD:
    c=payload[f'CHIRPS_{field}_l0'];i=payload[f'IMERG_{field}_l0']
    for month in range(12):
        a=full_maps[f'CHIRPS_{field}_l0'].pearson.values[month];b=full_maps[f'IMERG_{field}_l0'].pearson.values[month]
        ok=np.isfinite(a)&np.isfinite(b);a=a[ok];b=b[ok]
        w=np.broadcast_to(np.cos(np.deg2rad(c['lat']))[:,None],(len(c['lat']),len(c['lon'])))[ok]
        ma=np.average(a,weights=w);mb=np.average(b,weights=w)
        corr=np.sum(w*(a-ma)*(b-mb))/np.sqrt(np.sum(w*(a-ma)**2)*np.sum(w*(b-mb)**2))
        comparisons.append(dict(field=field,month=month+1,mean_abs_delta=float(np.average(np.abs(a-b),weights=w))))
pd.DataFrame(comparisons).to_csv(OUT/'sensibilidad_CHIRPS_IMERG.csv',index=False)
summary=dict(combinations=combos,calendar_months=12,primary_combinations=9,primary_maps_per_statistic=108,
             supplementary_Q_lag1_combinations=3,total_maps=288,response_period='1998-2022',n_response=285,
             monthly_n=common.groupby(common.index.month).size().to_dict(),reference='mismas 285 fechas completas de cuenca',
             minimum_pairs=20,lag_positive='campo climático anterior a la respuesta',
             no_inference='Coeficientes descriptivos, sin pruebas de significancia o atribución causal. 5.3 evaluará robustez.',
             local_station='Zaragoza: 14 meses completos; no se pueden estimar doce correlaciones interanuales locales.',
             regions=REGIONS,fields=attrs,
             outputs_sha256={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in OUT.glob('*.nc')})
(OUT/'resultados.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print('5.2 calculado: 108 mapas base por estadístico + 36 por estadístico para Q con ℓ=1.',flush=True)
