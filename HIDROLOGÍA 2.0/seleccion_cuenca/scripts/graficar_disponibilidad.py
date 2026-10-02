from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

O=Path(__file__).resolve().parents[1]/'resultados'
d=pd.read_csv(O/'disponibilidad_mensual_candidatas.csv',parse_dates=['mes'])
fig,axes=plt.subplots(3,1,figsize=(13,8),sharex=True,layout='constrained')
for ax,(code,name) in zip(axes,[(12027050,'Mulatos — Pueblo Nuevo'),(22027020,'Atá — Gaitania'),(26127040,'La Vieja — Cartago')]):
    x=d[d.gauge_id==code].copy()
    x['ano']=x.mes.dt.year
    x['mes_num']=x.mes.dt.month
    x['porcentaje']=100*x.Caudal/x.dias_esperados
    matrix=x.pivot(index='mes_num',columns='ano',values='porcentaje')
    im=ax.imshow(matrix,vmin=0,vmax=100,cmap='YlGn',aspect='auto',origin='lower',extent=[1980.5,2022.5,0.5,12.5])
    ax.set_title(f'{name} · {code}',loc='left')
    ax.set_yticks([1,3,6,9,12],['Ene','Mar','Jun','Sep','Dic'])
axes[-1].set_xlabel('Año')
fig.colorbar(im,ax=axes,label='Días con caudal disponible por mes (%)',shrink=.8)
fig.suptitle('Disponibilidad diaria dentro de cada mes · CAMELS-COL\nCalendario reconstruido; sin relleno de datos')
fig.savefig(O/'disponibilidad_candidatas.png',dpi=180)
