"""Síntesis cuantitativa para 5.4; no selecciona un nuevo rezago óptimo."""
from pathlib import Path
import json,importlib.util,hashlib
from datetime import datetime
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
from scipy import stats

ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'la_vieja/documentos';OUT=DOCS/'apartado_5_4';OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('robust',Path(__file__).with_name('48_calcular_robustez_5_3.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
RESPONSE={'CHIRPS':'P_CHIRPS_mm','IMERG':'P_IMERG_poligono_mm','Q':'Q_m3_s'}
df=pd.read_csv(DOCS/'imerg_poligono/series_alineadas.csv',parse_dates=['mes']).set_index('mes')
columns=list(RESPONSE.values())+['R_mm','Tmedia_ERA5_Land_C'];df=df.loc['1998-01-01':'2022-12-01',columns].dropna();assert len(df)==285
clim=df.groupby(df.index.month).agg(['mean','std','count']);clim.columns=['_'.join(c) for c in clim.columns];clim.index.name='mes_calendario';clim.to_csv(OUT/'climatologia_comun.csv')
an=df-df.groupby(df.index.month).transform('mean')
noaa=OUT/'NOAA_PSL_nina34.anom.data'
if not noaa.exists():
    import requests
    r=requests.get('https://psl.noaa.gov/data/correlation/nina34.anom.data',timeout=45);r.raise_for_status();noaa.write_bytes(r.content)
lines=noaa.read_text(encoding='utf-8').splitlines();data=[]
for line in lines[1:]:
    parts=line.split()
    if len(parts)!=13:continue
    try:year=int(parts[0]);values=list(map(float,parts[1:]))
    except ValueError:continue
    for month,value in enumerate(values,1):data.append((pd.Timestamp(year,month,1),np.nan if value==-99.99 else value))
index=pd.Series(dict(data),name='Nino34_NOAA_PSL_C').sort_index()
assert 'ERSST V6' in noaa.read_text() and '1981-2010' in noaa.read_text()
index=index.reindex(df.index);assert index.notna().all()
index=index-index.groupby(index.index.month).transform('mean')
records=[]
for response,col in RESPONSE.items():
    for month in range(1,13):
        selected=df.index.month==month;years=df.index.year[selected].to_numpy()
        x=index[selected].to_numpy()[:,None];y=an.loc[selected,col].to_numpy()
        a,b=mod.detrend(x,y,years);r,n=mod.corr(a,b);info=mod.inference(a,b,years,True)
        records.append({'response':response,'month':month,'n':int(n[0]),'r_detrended':float(r[0]),'rho_detrended':float(stats.spearmanr(a[:,0],b[:,0]).statistic),'neff':float(info['neff'][0]),'p_AR1':float(info['p'][0])})
idx=pd.DataFrame(records);valid=idx.p_AR1.notna();idx['q_BY_36']=np.nan;idx.loc[valid,'q_BY_36']=stats.false_discovery_control(idx.loc[valid,'p_AR1'],method='by');idx.to_csv(OUT/'contraste_NOAA_Nino34.csv',index=False)
pd.concat([df,index],axis=1).to_csv(OUT/'datos_contraste_indice.csv',index_label='mes')
(OUT/'indice_NOAA_metadatos.json').write_text(json.dumps({'url':'https://psl.noaa.gov/data/correlation/nina34.anom.data','source_description':'NOAA PSL Niño 3.4; ERSST V6; 5N-5S,170W-120W','original_reference':'1981-2010','analysis_reference':'mismos 285 meses de cuenca 1998-2022; OLS mensual retira tendencia','units':'degC','sentinel':-99.99,'sha256':hashlib.sha256(noaa.read_bytes()).hexdigest(),'retrieved_at':datetime.now(ZoneInfo('America/Bogota')).isoformat(),'inferential_family':'36 contrastes complementarios: 3 respuestas x 12 meses; ell=0; BY; no se mezcla con la familia de mapas','no_ONI':'Índice mensual no suavizado; no se clasifican episodios oficiales con umbral ONI','version_difference':'Índice V6; campos 5.2-5.3 V5. No es una validación independiente ni una atribución causal.'},ensure_ascii=False,indent=2),encoding='utf-8')

# Region boxes fixed for interpretation, not claimed as independent confirmations.
REGIONS={'Pacifico_ecuatorial':(-10,10,-180,-80),'Caribe':(10,20,-85,-60),'Atlantico_tropical_norte':(5,25,-55,-15),'Atlantico_tropical_oriental':(-25,10,-25,15),'Colombia_contexto':(-5,15,-85,-65)}
rows=[];dependencies=[]
for response in RESPONSE:
    for field in ['sst','slp','z500']:
        for lag in [0,1] if response=='Q' else [0]:
            key=f'{response}_{field}_l{lag}';ds=mod.reader.load(DOCS/f'apartado_5_3/{key}.nc')
            w=np.broadcast_to(np.cos(np.deg2rad(ds.lat.values))[:,None],ds.r_detrended.shape[1:])
            for month in range(1,13):
                s=ds.sel(month=month)
                for region,(south,north,west,east) in REGIONS.items():
                    box=(ds.lat.values[:,None]>=south)&(ds.lat.values[:,None]<=north)&(ds.lon.values[None,:]>=west)&(ds.lon.values[None,:]<=east)
                    valid=box&np.isfinite(s.r_detrended.values);weights=np.where(valid,w,np.nan)
                    candidates=valid&(s.candidate_by_stable.values>0)
                    rows.append({'response':response,'field':field,'lag':lag,'month':month,'region':region,'r_mean':mod.wmean(s.r_detrended.values,weights),'n_cells':int(valid.sum()),'positive_area_pct':100*mod.wmean((s.r_detrended.values>0).astype(float),weights),'candidate_area_pct':100*mod.wmean((s.candidate_by_stable.values>0).astype(float),weights),'candidate_cells':int(candidates.sum()),'candidate_r_min':float(np.min(s.r_detrended.values[candidates])) if candidates.any() else np.nan,'candidate_r_max':float(np.max(s.r_detrended.values[candidates])) if candidates.any() else np.nan})
            print('Regiones',key,flush=True)
    # Dependence between the fields as region means, not independent causal effects.
    dates=df.index;field_series={}
    for field in ['sst','slp','z500']:
        var={'sst':'sst_anomaly','slp':'slp_anomaly','z500':'z500_anomaly'}[field]
        ds=mod.reader.load(DOCS/f'apartado_5_1/{field}_anomalias_285_meses.nc')
        bounds=(-5,5,-170,-120) if field=='sst' else (-5,15,-85,-65)
        south,north,west,east=bounds;a=ds[var].sel(lat=slice(south,north),lon=slice(west,east))
        field_series[field]=a.weighted(np.cos(np.deg2rad(a.lat))).mean(('lat','lon')).values
    for month in range(1,13):
        mask=dates.month==month;years=dates.year[mask].to_numpy()
        for a,b in [('sst','slp'),('sst','z500'),('slp','z500')]:
            x,y=mod.detrend(field_series[a][mask,None],field_series[b][mask],years)
            r,n=mod.corr(x,y);dependencies.append({'month':month,'field1':a,'field2':b,'r_detrended':float(r[0]),'n':int(n[0]),'scope':'diagnóstico regional, no causal ni prueba independiente'})
    break
# All responses still need all regional maps; the break above avoids repeated identical field diagnoses.
for response in ['IMERG','Q']:
    for field in ['sst','slp','z500']:
        for lag in [0,1] if response=='Q' else [0]:
            key=f'{response}_{field}_l{lag}';ds=mod.reader.load(DOCS/f'apartado_5_3/{key}.nc');w=np.broadcast_to(np.cos(np.deg2rad(ds.lat.values))[:,None],ds.r_detrended.shape[1:])
            for month in range(1,13):
                s=ds.sel(month=month)
                for region,(south,north,west,east) in REGIONS.items():
                    box=(ds.lat.values[:,None]>=south)&(ds.lat.values[:,None]<=north)&(ds.lon.values[None,:]>=west)&(ds.lon.values[None,:]<=east);valid=box&np.isfinite(s.r_detrended.values);weights=np.where(valid,w,np.nan);candidates=valid&(s.candidate_by_stable.values>0)
                    rows.append({'response':response,'field':field,'lag':lag,'month':month,'region':region,'r_mean':mod.wmean(s.r_detrended.values,weights),'n_cells':int(valid.sum()),'positive_area_pct':100*mod.wmean((s.r_detrended.values>0).astype(float),weights),'candidate_area_pct':100*mod.wmean((s.candidate_by_stable.values>0).astype(float),weights),'candidate_cells':int(candidates.sum()),'candidate_r_min':float(np.min(s.r_detrended.values[candidates])) if candidates.any() else np.nan,'candidate_r_max':float(np.max(s.r_detrended.values[candidates])) if candidates.any() else np.nan})
            print('Regiones',key,flush=True)
pd.DataFrame(rows).to_csv(OUT/'regiones_coherentes.csv',index=False);pd.DataFrame(dependencies).to_csv(OUT/'dependencias_campos.csv',index=False)

# Monthly rain-Q correlations use calendar lags, preserving missing dates.
lagrows=[]
complete=pd.date_range('1998-01-01','2022-12-01',freq='MS');af=an.reindex(complete)
for response in ['CHIRPS','IMERG']:
    for lag in [0,1,2]:
        x=af[RESPONSE[response]];y=af.Q_m3_s.shift(-lag);valid=x.notna()&y.notna();lagrows.append({'response':response,'rain_precedes_Q_months':lag,'n':int(valid.sum()),'r_anomalies':float(stats.pearsonr(x[valid],y[valid]).statistic)})
pd.DataFrame(lagrows).to_csv(OUT/'lluvia_caudal_rezagos.csv',index=False)
spec4=json.loads((OUT/'d42_fuente_punto4.json').read_text(encoding='utf-8'));spectral=[]
for r in spec4['rows']:
    if r['n']!=73:continue
    variable='CHIRPS' if 'CHIRPS' in r['variable'] else 'IMERG' if 'IMERG' in r['variable'] else 'Q' if 'Caudal' in r['variable'] else 'T'
    spectral.append({'variable':variable,'transformation':r['transformation'],'n':73,'start':'1998-01','end':'2004-01','annual_pct':r['annual']['band_share_pct'],'semiannual_pct':r['semiannual']['band_share_pct'],'interannual_pct':r['interannual_2_10y']['band_share_pct'],'interannual_peak_months':r['interannual_2_10y']['period_months'],'cycles_observed':r['interannual_2_10y']['cycles_observed']})
pd.DataFrame(spectral).to_csv(OUT/'sintesis_fourier.csv',index=False)
assert len(spectral)==8
metrics={'n_common':285,'period':'1998-2022','CHIRPS_climatological_annual_mm':float(clim.P_CHIRPS_mm_mean.sum()),'IMERG_climatological_annual_mm':float(clim.P_IMERG_poligono_mm_mean.sum()),'Q_mean_m3_s':float(df.Q_m3_s.mean()),'T_mean_C':float(df.Tmedia_ERA5_Land_C.mean()),
 'peaks':{v:{'peak_month':int(clim[c+'_mean'].idxmax()),'min_month':int(clim[c+'_mean'].idxmin()),'peak_value':float(clim[c+'_mean'].max()),'min_value':float(clim[c+'_mean'].min())} for v,c in RESPONSE.items()},
 'index_B_Y_months':idx.loc[idx.q_BY_36<=.05,['response','month','r_detrended','q_BY_36']].to_dict('records'),
 'hypothesis_scope':'No se encontró una formulación inicial explícita documentada; se declara la hipótesis operativa retrospectiva, sin atribuirla al grupo como prerregistro.',
 'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('*.csv')}}
(OUT/'resultados.json').write_text(json.dumps(metrics,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(metrics,ensure_ascii=False),flush=True)
