from pathlib import Path
import pandas as pd,json
r=Path('revision_github_2026-10-05/proyecto');d=pd.read_csv(r/'la_vieja/documentos/imerg_poligono/series_alineadas.csv',parse_dates=['mes']).set_index('mes').asfreq('MS');l=pd.read_csv(next(r.rglob('*Zaragoza_mensual*.csv')),parse_dates=['mes']).set_index('mes');d['L']=l.lluvia_local_mm.where(l.n_intervalos==l.esperados); d=d.rename(columns={'P_IMERG_poligono_mm':'I','Q_m3_s':'Q','R_mm':'R'});d=d.loc['1998':'2022'];a=d[['I','Q','R']]-d[['I','Q','R']].groupby(d.index.month).transform('mean');
for x,y in [('I','L'),('L','Q'),('I','Q'),('I','R')]:
 z=d[[x,y]].dropna(); print(x,y,len(z),'pearson',z[x].corr(z[y]),'spearman',z[x].corr(z[y],method=lambda u,v: pd.Series(u).rank().corr(pd.Series(v).rank())))
 if y=='L': e=z[x]-z[y];print('errores',e.mean(),e.abs().mean(),(e.pow(2).mean())**.5)
 vals=[]
 for k in range(4):
  b=pd.concat([d[x].shift(k).rename('x'),d[y].rename('y')],axis=1).dropna(); vals.append((k,len(b),b.x.corr(b.y),b.x.corr(b.y,method=lambda u,v: pd.Series(u).rank().corr(pd.Series(v).rank()))))
 print('rezagos',vals)
 if x=='I' and y in ['Q','R']:print('anom',a[x].corr(a[y]),a[x].corr(a[y],method=lambda u,v: pd.Series(u).rank().corr(pd.Series(v).rank())))
 print('extremos',z.nlargest(2,y).to_string())

