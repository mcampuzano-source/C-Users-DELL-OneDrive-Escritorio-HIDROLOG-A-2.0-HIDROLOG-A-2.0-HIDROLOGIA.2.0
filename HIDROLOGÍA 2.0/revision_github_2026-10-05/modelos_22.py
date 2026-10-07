from pathlib import Path
import json
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
DOC=ROOT/'proyecto/la_vieja/documentos'
OUT=DOC/'apartado_2_2';OUT.mkdir(exist_ok=True)
d=pd.read_csv(DOC/'imerg_poligono/series_alineadas.csv',parse_dates=['mes']).set_index('mes').asfreq('MS').loc['1998':'2022']
d=d.rename(columns={'P_IMERG_poligono_mm':'IMERG','P_CHIRPS_mm':'CHIRPS','Q_m3_s':'Q'})
l=pd.read_csv(next((ROOT/'proyecto').rglob('*Zaragoza_mensual*.csv')),parse_dates=['mes']).set_index('mes')
d['local']=l.lluvia_local_mm.where(l.n_intervalos==l.esperados)
for src in ['IMERG','CHIRPS']:d[src+'_lag1']=d[src].shift(1)
q=d[['Q','IMERG','CHIRPS','IMERG_lag1','CHIRPS_lag1']].dropna()
dev=q.loc[:'2016-12'];holdout=q.loc['2017-01':]
FOLDS=[('1998-01','2006-12','2007-01','2009-12'),('1998-01','2009-12','2010-01','2012-12'),('1998-01','2012-12','2013-01','2016-12')]
KINDS=['media','climatologia','lineal','rezago1','lineal_rezago','raiz']
def matrix(frame,src,kind):
 x=frame[src].to_numpy()
 return {'lineal':lambda:np.column_stack([np.ones(len(frame)),x]),'rezago1':lambda:np.column_stack([np.ones(len(frame)),frame[src+'_lag1']]),'lineal_rezago':lambda:np.column_stack([np.ones(len(frame)),x,frame[src+'_lag1']]),'raiz':lambda:np.column_stack([np.ones(len(frame)),np.sqrt(x)])}[kind]()
def fit(train,src,kind,target):
 y=train[target].to_numpy()
 if kind=='media':return dict(kind=kind,coef=[float(y.mean())],p=1)
 if kind=='climatologia':return dict(kind=kind,monthly=train.groupby(train.index.month)[target].mean().to_dict(),coef=[],p=12)
 X=matrix(train,src,kind);b=np.linalg.lstsq(X,y,rcond=None)[0]
 return dict(kind=kind,coef=b.tolist(),p=X.shape[1],condition=float(np.linalg.cond(X)))
def predict(model,frame,src):
 kind=model['kind']
 if kind=='media':raw=np.full(len(frame),model['coef'][0])
 elif kind=='climatologia':raw=np.array([model['monthly'][m] for m in frame.index.month])
 else:raw=matrix(frame,src,kind)@np.array(model['coef'])
 return np.maximum(raw,0),int(np.sum(raw<0))
def metric(y,p):
 e=p-y;den=np.sum((y-y.mean())**2)
 return dict(RMSE=float(np.sqrt(np.mean(e**2))),MAE=float(np.mean(np.abs(e))),sesgo=float(e.mean()),R2=float(1-np.sum(e**2)/den) if den>0 else None)
cv=[];preds=[];fits={};folds=[]
for src in ['IMERG','CHIRPS']:
 for kind in KINDS:
  records=[]
  for k,(t0,t1,v0,v1) in enumerate(FOLDS,1):
   tr=dev.loc[t0:t1];va=dev.loc[v0:v1];model=fit(tr,src,kind,'Q');p,clipped=predict(model,va,src)
   row=dict(fuente=src,modelo=kind,bloque=k,n_ajuste=len(tr),n_validacion=len(va),**metric(va.Q.to_numpy(),p),negativos_truncados=clipped);folds.append(row)
   for date,y,yp in zip(va.index,va.Q,p):records.append(dict(mes=date.strftime('%Y-%m'),observado=y,estimado=yp,fuente=src,modelo=kind,bloque=k))
  pooled=pd.DataFrame(records);cv.append(dict(fuente=src,modelo=kind,n=len(pooled),**metric(pooled.observado.to_numpy(),pooled.estimado.to_numpy()),parametros=fit(dev,src,kind,'Q')['p']))
  preds.extend(records);fits[src+'_'+kind]=fit(dev,src,kind,'Q')
cv=pd.DataFrame(cv);selected={}
for src in ['IMERG','CHIRPS']:
 rows=cv.query('fuente==@src');candidates=rows[~rows.modelo.isin(['media','climatologia'])].sort_values('RMSE');best=candidates.iloc[0]
 # Require a clear gain before adding a third coefficient to a two-parameter relation.
 simple=candidates[candidates.parametros==2].iloc[0]
 if best.parametros>2 and (simple.RMSE-best.RMSE)/simple.RMSE<.05:best=simple
 baseline=rows[rows.modelo.isin(['media','climatologia'])].sort_values('RMSE').iloc[0]
 selected[src]=dict(modelo=best.modelo,modelo_coef=fits[src+'_'+best.modelo],CV_RMSE=float(best.RMSE),baseline=baseline.modelo,baseline_RMSE=float(baseline.RMSE),ganancia_vs_baseline_pct=float(100*(baseline.RMSE-best.RMSE)/baseline.RMSE),candidato_util=bool(best.RMSE<baseline.RMSE*.95),n_ajuste=len(dev),periodo_ajuste=['1998-01','2016-12'],rango_P=[float(dev[src].min()),float(dev[src].max())],rango_Q=[float(dev.Q.min()),float(dev.Q.max())])
local=d[['local','IMERG','CHIRPS']].dropna();local_stats=[];local_fits={};local_preds=[]
for src in ['IMERG','CHIRPS']:
 for kind in ['media','lineal','raiz']:
  model=fit(local,src,kind,'local');p,clip=predict(model,local,src)
  tr=local.loc['2018'];va=local.loc['2019'];mtemp=fit(tr,src,kind,'local');pv,ct=predict(mtemp,va,src)
  row=dict(fuente=src,modelo=kind,n_ajuste=len(local),**{'ajuste_'+k:v for k,v in metric(local.local.to_numpy(),p).items()},n_temporal_ajuste=len(tr),n_temporal_validacion=len(va),**{'temporal_'+k:v for k,v in metric(va.local.to_numpy(),pv).items()},negativos_truncados_ajuste=clip,negativos_truncados_temporal=ct);local_stats.append(row)
  local_fits[src+'_'+kind]=dict(**model,rango_P=[float(local[src].min()),float(local[src].max())],n=14)
  for date,y,yp in zip(local.index,local.local,p):local_preds.append(dict(mes=date.strftime('%Y-%m'),fuente=src,modelo=kind,observado=y,estimado=yp))
ql=d[['local','Q']].dropna();qlocal=[];qlocal_coefs={}
for kind in ['media','lineal','raiz']:
 model=fit(ql,'local',kind,'Q');pa,ca=predict(model,ql,'local');tr=ql.loc['2018'];va=ql.loc['2019'];mt=fit(tr,'local',kind,'Q');pv,ct=predict(mt,va,'local')
 qlocal.append(dict(modelo=kind,n_ajuste=len(ql),**{'ajuste_'+k:v for k,v in metric(ql.Q.to_numpy(),pa).items()},n_validacion=len(va),**{'temporal_'+k:v for k,v in metric(va.Q.to_numpy(),pv).items()}));qlocal_coefs[kind]=model
cv.to_csv(OUT/'comparacion_Q_validacion_desarrollo.csv',index=False);pd.DataFrame(folds).to_csv(OUT/'bloques_validacion_Q.csv',index=False);pd.DataFrame(preds).to_csv(OUT/'estimaciones_Q_desarrollo.csv',index=False);pd.DataFrame(local_stats).to_csv(OUT/'comparacion_lluvia_local.csv',index=False);pd.DataFrame(local_preds).to_csv(OUT/'estimaciones_local_ajuste.csv',index=False)
dev.to_csv(OUT/'muestra_Q_desarrollo.csv');local.to_csv(OUT/'muestra_local.csv')
pd.DataFrame(qlocal).to_csv(OUT/'modelos_Q_lluvia_local.csv',index=False)
result=dict(Q_modelos=selected,Q_coeficientes=fits,local_coeficientes=local_fits,local_resultados=local_stats,Q_local_resultados=qlocal,Q_local_coeficientes=qlocal_coefs,folds=FOLDS,n_desarrollo=len(dev),n_reserva_2_3=len(holdout),periodo_reserva=['2017-01','2022-12'],reserva_evaluada=False)
(OUT/'resultados.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
