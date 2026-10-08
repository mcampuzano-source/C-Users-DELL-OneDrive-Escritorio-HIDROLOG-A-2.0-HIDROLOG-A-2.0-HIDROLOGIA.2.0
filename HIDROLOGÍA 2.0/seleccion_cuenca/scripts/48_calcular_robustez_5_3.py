"""Robustez 5.3: tendencias, dependencia anual, FDR global y estabilidad.

Sin descargar ni modificar observaciones. Familia inferencial única: Pearson,
ambas representaciones, 12 combinaciones x 12 meses x celdas válidas.
"""
from pathlib import Path
import importlib.util, json, hashlib, tempfile, shutil, base64
import numpy as np
import pandas as pd
import xarray as xr
from scipy import stats, ndimage

ROOT=Path(__file__).resolve().parents[1]
DOCS=ROOT/'la_vieja/documentos'
OUT=DOCS/'apartado_5_3';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('reader',Path(__file__).with_name('41_descargar_campos_globales.py'))
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
COMBOS=json.loads((DOCS/'apartado_5_2/resultados.json').read_text(encoding='utf-8'))['combinations']
COLUMNS={'CHIRPS':'P_CHIRPS_mm','Q':'Q_m3_s','IMERG':'P_IMERG_poligono_mm'}
source=DOCS/'imerg_poligono/series_alineadas.csv'
df=pd.read_csv(source,parse_dates=['mes']).set_index('mes')
df=df.loc['1998-01-01':'2022-12-01',list(COLUMNS.values())].dropna()
assert len(df)==285
anom=df-df.groupby(df.index.month).transform('mean')

def paired(x,y):
    x=np.asarray(x,float);y=np.broadcast_to(np.asarray(y,float).reshape(-1,1),x.shape).copy()
    ok=np.isfinite(x)&np.isfinite(y)
    return np.where(ok,x,np.nan),np.where(ok,y,np.nan),ok

def corr(x,y):
    if y.ndim==1:y=np.broadcast_to(y[:,None],x.shape)
    ok=np.isfinite(x)&np.isfinite(y);n=ok.sum(0);den=np.maximum(n,1)
    xx=np.where(ok,x,0);yy=np.where(ok,y,0)
    dx=np.where(ok,xx-xx.sum(0)/den,0);dy=np.where(ok,yy-yy.sum(0)/den,0)
    div=np.sqrt((dx*dx).sum(0)*(dy*dy).sum(0))
    r=np.divide((dx*dy).sum(0),div,out=np.full(x.shape[1],np.nan),where=div>1e-14)
    return np.clip(r,-1,1),n

def detrend(x,y,years):
    x,y,ok=paired(x,y) if y.ndim==1 else (x,y,np.isfinite(x)&np.isfinite(y))
    n=ok.sum(0);den=np.maximum(n,1)
    t=np.broadcast_to(np.asarray(years,float)[:,None],x.shape)
    tt=np.where(ok,t,0);mx=np.nansum(x,0)/den;my=np.nansum(y,0)/den;mt=tt.sum(0)/den
    dt=np.where(ok,t-mt,0);dx=np.where(ok,x-mx,0);dy=np.where(ok,y-my,0)
    vt=(dt*dt).sum(0)
    bx=np.divide((dt*dx).sum(0),vt,out=np.zeros(x.shape[1]),where=vt>0)
    by=np.divide((dt*dy).sum(0),vt,out=np.zeros(x.shape[1]),where=vt>0)
    return np.where(ok,dx-bx*dt,np.nan),np.where(ok,dy-by*dt,np.nan)

def inference(x,y,years,dt=False):
    x,y,ok=paired(x,y) if y.ndim==1 else (x,y,np.isfinite(x)&np.isfinite(y))
    r,n=corr(x,y)
    consecutive=np.diff(years)==1
    valid=ok[1:]&ok[:-1]&consecutive[:,None]
    rx,na=corr(np.where(valid,x[:-1],np.nan),np.where(valid,x[1:],np.nan))
    ry,_=corr(np.where(valid,y[:-1],np.nan),np.where(valid,y[1:],np.nan))
    # AR(1) approximation for correlation, not the ESS formula for a mean.
    prod=rx*ry
    ess=np.clip(n*(1-prod)/(1+prod),3,n)
    dfree=ess-(3 if dt else 2)
    tval=np.abs(r)*np.sqrt(np.maximum(dfree,0)/np.maximum(1-r*r,1e-15))
    p=2*stats.t.sf(tval,dfree)
    good=(n>=20)&(na>=10)&(dfree>1)&np.isfinite(r)&np.isfinite(ess)
    return {k:np.where(good,v,np.nan) for k,v in [('r',r),('neff',ess),('p',p),('rho1_field',rx),('rho1_response',ry)]}|{'n':n,'n_adjacent':na}

def wmean(a,w):
    ok=np.isfinite(a)&np.isfinite(w)
    return float(np.average(a[ok],weights=w[ok])) if ok.any() and w[ok].sum()>0 else float('nan')

def pattern(a,b,w):
    ok=np.isfinite(a)&np.isfinite(b)&(w>0)
    if ok.sum()<3:return float('nan')
    a=a[ok];b=b[ok];w=w[ok];a=a-np.average(a,weights=w);b=b-np.average(b,weights=w)
    den=np.sqrt(np.sum(w*a*a)*np.sum(w*b*b))
    return float(np.sum(w*a*b)/den) if den>0 else float('nan')

def largest(mask):
    labels,n=ndimage.label(mask,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))
    if not n:return 0
    parent=np.arange(n+1)
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for a,b in zip(labels[:,0],labels[:,-1]):
        if a and b:parent[find(a)]=find(b)
    counts=np.bincount(labels.ravel(),minlength=n+1);merged={}
    for a in range(1,n+1):root=find(a);merged[root]=merged.get(root,0)+int(counts[a])
    return max(merged.values())

def validate():
    rng=np.random.default_rng(721);t=np.array([1998,1999,2001,2002,2003,2005,2006,2007,2008,2009,2010,2011],float)
    x=rng.normal(size=(12,3))+t[:,None]*.3;y=rng.normal(size=12)+t*.6;x[3,1]=np.nan
    a,b=detrend(x,y,t)
    for j in range(3):
        good=np.isfinite(x[:,j]);design=np.c_[np.ones(good.sum()),t[good]-t[good].mean()]
        ex=x[good,j]-design@np.linalg.lstsq(design,x[good,j],rcond=None)[0]
        ey=y[good]-design@np.linalg.lstsq(design,y[good],rcond=None)[0]
        assert np.allclose(a[good,j],ex,atol=1e-9)
        assert np.allclose(b[good,j],ey,atol=1e-9)
        assert abs(corr(a,b)[0][j]-stats.pearsonr(ex,ey).statistic)<1e-9
    assert np.array_equal(inference(x,y,t)['n_adjacent'],[9,7,9])
    assert largest(np.array([[1,0,1],[1,0,0]],bool))==3
    return {'OLS_pairwise_missing_and_real_years':'passed','gap_autocorrelation':'passed','cyclic_longitude_components':'passed'}

def main():
    validation=validate();maps={};checks=[]
    fields={}
    for field,var in [('sst','sst'),('slp','slp'),('z500','hgt')]:
        p=ROOT/f'datos/clima_global_5_1/{field}_1981_2022.nc'
        ds=reader.load(p);da=ds[var].squeeze(drop=True).reset_coords(drop=True).astype('float64')
        if field=='slp' and str(da.attrs.get('units','')).lower()=='pa':da=da/100
        da=da.assign_coords(lon=((da.lon+180)%360)-180).sortby('lon').sortby('lat')
        if field=='z500':
            ps=reader.load(ROOT/'datos/clima_global_5_1/psfc_1981_2022.nc')['pres'].squeeze(drop=True).reset_coords(drop=True)
            if str(ps.attrs.get('units','')).lower()=='pa':ps=ps/100
            ps=ps.assign_coords(lon=((ps.lon+180)%360)-180).sortby('lon').sortby('lat');da=da.where(ps>=500)
        clim=da.sel(time=df.index).groupby('time.month').mean('time',skipna=True)
        fields[field]=(da.groupby('time.month')-clim).transpose('time','lat','lon')
        print('Campo listo:',field,flush=True)
    for combo in COMBOS:
        key=combo['key'];response=combo['response'];field=combo['field'];lag=combo['lag']
        da=fields[field];climate_dates=df.index-pd.DateOffset(months=lag)
        xall=da.sel(time=climate_dates).values.reshape(285,-1);yall=anom[COLUMNS[response]].values
        old=reader.load(DOCS/f'apartado_5_2/{key}.nc')
        records=[]
        for month in range(1,13):
            rows=df.index.month==month;years=df.index.year[rows].to_numpy()
            x,y,ok=paired(xall[rows],yall[rows]);a,b=detrend(x,y,years)
            orig=inference(x,y,years);dt=inference(a,b,years,True)
            # Coefficients retain original >=20 threshold even if inference unavailable.
            ro,n=corr(x,y);rd,_=corr(a,b);valid=(n>=20)&np.isfinite(ro)&np.isfinite(rd)
            ro=np.where(valid,ro,np.nan);rd=np.where(valid,rd,np.nan)
            shape=(da.sizes['lat'],da.sizes['lon'])
            err=np.nanmax(np.abs(ro.reshape(shape)-old.pearson.sel(month=month).values))
            assert err<1e-10
            checks.append({'key':key,'month':month,'original_map_max_error':float(err)})
            split=[];ns=[]
            for selected in [years<=2009,years>=2010]:
                ax,by=detrend(x[selected],y[selected],years[selected]);rsub,nsub=corr(ax,by)
                split.append(np.where(nsub>=10,rsub,np.nan));ns.append(nsub)
            loo=[]
            for i in range(len(years)):
                selected=np.arange(len(years))!=i;ax,by=detrend(x[selected],y[selected],years[selected]);rl,nl=corr(ax,by)
                loo.append(np.where(nl>=19,rl,np.nan))
            loo=np.asarray(loo);goodloo=np.isfinite(loo)
            delta=np.max(np.where(goodloo,np.abs(loo-rd),-np.inf),axis=0);delta=np.where(goodloo.any(0),delta,np.nan)
            loomin=np.min(np.where(goodloo,loo,np.inf),axis=0);loomax=np.max(np.where(goodloo,loo,-np.inf),axis=0)
            # Both extrema of the response are explicitly removed together, refitting OLS.
            finite_y=np.nanmean(y,axis=1);extreme=np.argsort(np.abs(finite_y))[-2:]
            selected=~np.isin(np.arange(len(years)),extreme);ax,by=detrend(x[selected],y[selected],years[selected]);rex,nex=corr(ax,by)
            rex=np.where(nex>=18,rex,np.nan)
            rho=corr(stats.rankdata(a,axis=0,nan_policy='omit'),stats.rankdata(b,axis=0,nan_policy='omit'))[0]
            row={'r_original':ro,'r_detrended':rd,'r_spearman_detrended':np.where(valid,rho,np.nan),'n_pairs':n,
                 'neff_original':orig['neff'],'neff_detrended':dt['neff'],'p_original':orig['p'],'p_detrended':dt['p'],
                 'rho1_field':dt['rho1_field'],'rho1_response':dt['rho1_response'],'n_adjacent':dt['n_adjacent'],
                 'r_1998_2009':split[0],'r_2010_2022':split[1],'n_1998_2009':ns[0],'n_2010_2022':ns[1],
                 'loo_max_delta':np.where(valid,delta,np.nan),'loo_min':np.where(valid,loomin,np.nan),'loo_max':np.where(valid,loomax,np.nan),
                 'r_without_two_extremes':np.where(valid,rex,np.nan)}
            records.append({k:v.reshape(shape) for k,v in row.items()})
        ds=xr.Dataset({k:(('month','lat','lon'),np.array([r[k] for r in records])) for k in records[0]},coords={'month':np.arange(1,13),'lat':da.lat,'lon':da.lon})
        ds.attrs.update(response=response,field=field,lag_months=lag,reference='1998-2022; mismas 285 fechas completas de cuenca',minimum_pairs=20,subperiod_minimum_pairs=10,
                        detrending='OLS de ambas variables por mes, celda y mismos pares; años reales',inference='Aproximación AR(1) sobre años consecutivos, no meses; n_eff capado en [3,n]',
                        family='Pearson original y detrended, todas las combinaciones, meses, celdas y rezagos',response_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
        maps[key]=ds
        print('Calculado',key,flush=True)
    # Invalid p values are excluded, never turned into discoveries.
    refs=[];pvals=[]
    for key,ds in maps.items():
        for rep in ['original','detrended']:
            a=ds['p_'+rep].values;mask=np.isfinite(a);refs.append((key,rep,mask,int(mask.sum())));pvals.append(a[mask])
    pv=np.concatenate(pvals);bh=stats.false_discovery_control(pv,method='bh');by=stats.false_discovery_control(pv,method='by')
    offset=0
    for key,rep,mask,size in refs:
        for method,values in [('bh',bh),('by',by)]:
            a=np.full(mask.shape,np.nan);a[mask]=values[offset:offset+size];maps[key]['q_'+method+'_'+rep]=( ('month','lat','lon'),a)
        offset+=size
    assert offset==len(pv)
    records=[];regions=[];source_sensitivity=[];payload={}
    region_defs={'Niño 3.4':(-5,5,-170,-120),'Atlántico tropical norte':(5,25,-55,-15),'Caribe':(10,20,-85,-60)}
    for key,ds in maps.items():
        w=np.broadcast_to(np.cos(np.deg2rad(ds.lat.values))[:,None],(ds.sizes['lat'],ds.sizes['lon']))
        stable=np.isfinite(ds.r_detrended)&(np.sign(ds.r_1998_2009)==np.sign(ds.r_detrended))&(np.sign(ds.r_2010_2022)==np.sign(ds.r_detrended))&(ds.loo_min*ds.loo_max>0)&(ds.loo_max_delta<=.2)&(np.abs(ds.r_detrended)>=.3)
        candidate=stable&(ds.q_by_detrended<=.05)
        ds['stable_descriptive']=stable.astype('int8');ds['candidate_by_stable']=candidate.astype('int8')
        for m in range(1,13):
            s=ds.sel(month=m);valid=np.isfinite(s.r_detrended.values);den=w[valid].sum();pct=lambda mask:float(100*w[mask&valid].sum()/den) if den else 0
            records.append({'key':key,'response':ds.attrs['response'],'field':ds.attrs['field'],'lag':ds.attrs['lag_months'],'month':m,
                'valid_cells':int(valid.sum()),'n_min':float(np.nanmin(s.n_pairs.values[valid])),'n_max':float(np.nanmax(s.n_pairs.values[valid])),
                'neff_min':float(np.nanmin(s.neff_detrended)),'neff_median':float(np.nanmedian(s.neff_detrended)),
                'mean_abs_detrend_delta':wmean(np.abs(s.r_original.values-s.r_detrended.values),w),
                'pattern_original_detrended':pattern(s.r_original.values,s.r_detrended.values,w),
                'pattern_subperiods':pattern(s.r_1998_2009.values,s.r_2010_2022.values,w),
                'fraction_sign_agree_subperiods_pct':pct((s.r_1998_2009.values*s.r_2010_2022.values)>0),
                'mean_loo_max_delta':wmean(s.loo_max_delta.values,w),'mean_abs_extreme_delta':wmean(np.abs(s.r_without_two_extremes.values-s.r_detrended.values),w),
                'area_p05_pct':pct(s.p_detrended.values<=.05),'area_bh_pct':pct(s.q_bh_detrended.values<=.05),'area_by_pct':pct(s.q_by_detrended.values<=.05),
                'by_cells':int((s.q_by_detrended.values<=.05).sum()),'area_stable_pct':pct(s.stable_descriptive.values>0),
                'area_candidate_pct':pct(s.candidate_by_stable.values>0),'candidate_cells':int(s.candidate_by_stable.sum()),'largest_connected_candidate_cells':largest(s.candidate_by_stable.values>0)})
            for region,(south,north,west,east) in region_defs.items():
                if ds.attrs['field']!='sst':continue
                mask=(ds.lat.values[:,None]>=south)&(ds.lat.values[:,None]<=north)&(ds.lon.values[None,:]>=west)&(ds.lon.values[None,:]<=east)
                weighted=w*mask;regions.append({'key':key,'region':region,'month':m,'r_area_mean':wmean(s.r_detrended.values,weighted),'sign_agree_pct':100*wmean(((s.r_1998_2009.values*s.r_2010_2022.values)>0).astype(float),np.where(valid,weighted,np.nan)),
                    'by_area_pct':100*wmean((s.q_by_detrended.values<=.05).astype(float),np.where(valid,weighted,np.nan)),
                    'candidate_area_pct':100*wmean((s.candidate_by_stable.values>0).astype(float),np.where(valid,weighted,np.nan))})
        path=OUT/(key+'.nc')
        with tempfile.TemporaryDirectory(prefix='robust_nc_') as tmp:
            p=Path(tmp)/'map.nc';ds.to_netcdf(p,engine='netcdf4',encoding={v:{'zlib':True,'complevel':4} for v in ds.data_vars});shutil.copyfile(p,path)
        # Binary little-endian payload: full native grids, coefficient precision 0.001.
        encoded={}
        for name in ['r_original','r_detrended','r_1998_2009','r_2010_2022','n_pairs','neff_detrended','loo_max_delta','q_by_detrended','candidate_by_stable']:
            v=ds[name].values;scale=1 if name in ['n_pairs','candidate_by_stable'] else 1000
            a=np.where(np.isfinite(v),np.rint(np.nan_to_num(v)*scale),-32768).astype('<i2')
            encoded[name]={'scale':scale,'data':base64.b64encode(a.tobytes()).decode('ascii')}
        payload[key]={'lat':ds.lat.values.tolist(),'lon':ds.lon.values.tolist(),'response':ds.attrs['response'],'field':ds.attrs['field'],'lag':int(ds.attrs['lag_months']),'layers':encoded}
    for field in ['sst','slp','z500']:
        a=maps[f'CHIRPS_{field}_l0'];b=maps[f'IMERG_{field}_l0'];w=np.broadcast_to(np.cos(np.deg2rad(a.lat.values))[:,None],a.r_detrended.shape[1:])
        for m in range(1,13):
            x=a.sel(month=m);y=b.sel(month=m);source_sensitivity.append({'field':field,'month':m,'pattern_detrended_CHIRPS_IMERG':pattern(x.r_detrended.values,y.r_detrended.values,w),'mean_abs_delta':wmean(np.abs(x.r_detrended.values-y.r_detrended.values),w)})
    summary=pd.DataFrame(records);regional=pd.DataFrame(regions);sens=pd.DataFrame(source_sensitivity)
    summary.to_csv(OUT/'resumen_mensual.csv',index=False);regional.to_csv(OUT/'regiones_sst.csv',index=False);sens.to_csv(OUT/'sensibilidad_fuentes.csv',index=False)
    pd.DataFrame(checks).to_csv(OUT/'verificacion_reproduccion_5_2.csv',index=False)
    for name,table in [('resumen_mensual',summary),('regiones_sst',regional),('sensibilidad_fuentes',sens)]:
        (OUT/(name+'.table.json')).write_text(table.to_json(orient='split',index=False,force_ascii=False),encoding='utf-8')
    metadata={'family_size':len(pv),'n_months':285,'minimum_years':20,'subperiod_minimum_years':10,'fdr_level':.05,'primary_fdr':'BY',
              'inference_limitation':'p aproximados AR(1), no garantía exacta finita; BY no corrige p mal calibrados. Persistencia de orden superior no evaluada.',
              'subperiods':['1998-2009','2010-2022'],'outlier_check':'exclusión individual de cada año y conjunta de dos extremos absolutos de respuesta; OLS se reajusta',
              'versions':{name:__import__(name).__version__ for name in ['numpy','pandas','scipy','xarray']},
              'validation':validation,'by_cells_total':int(summary.by_cells.sum()),'candidate_cells_total':int(summary.candidate_cells.sum()),
              'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.nc')}}
    (OUT/'resultados.json').write_text(json.dumps(metadata,indent=2,ensure_ascii=False),encoding='utf-8')
    (OUT/'mapas_binarios.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
    print('FINAL',json.dumps({k:metadata[k] for k in ['family_size','by_cells_total','candidate_cells_total']}),flush=True)

if __name__=='__main__':main()
