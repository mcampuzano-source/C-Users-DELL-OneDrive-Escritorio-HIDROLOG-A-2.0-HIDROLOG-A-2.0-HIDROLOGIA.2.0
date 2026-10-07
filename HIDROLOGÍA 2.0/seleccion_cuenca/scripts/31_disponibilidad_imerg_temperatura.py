"""Disponibilidad mensual por fuente; no atribuye cobertura diaria no comprobada."""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
OUT = DOC / 'disponibilidad_mensual'


def main():
    OUT.mkdir(exist_ok=True)
    calendar = pd.date_range('1981-01-01','2022-12-01',freq='MS')
    specs = [('IMERG polígono', DOC/'imerg_poligono'/'IMERG_mensual_poligono_1998_2022.csv',
              'P_IMERG_poligono_mm','1998-01-01'),
             ('ERA5-Land Tmedia', DOC/'temperatura_media_ERA5_Land_mensual.csv',
              'Tmedia_ERA5_Land_C','1981-01-01')]
    rows, matrices, summary = [], [], []
    for name,path,key,start in specs:
        source = pd.read_csv(path,parse_dates=['mes'])
        assert not source.mes.duplicated().any()
        assert source.mes.dt.is_month_start.all()
        assert source.mes.between(pd.Timestamp(start),pd.Timestamp('2022-12-01')).all()
        series = source.set_index('mes')[key].reindex(calendar)
        within = calendar >= pd.Timestamp(start)
        valid = np.isfinite(series.to_numpy())
        if key.startswith('P_'): valid &= series.to_numpy() >= 0
        states = np.where(~within,0,np.where(valid,2,1))
        matrices.append(states.reshape(42,12))
        for month,value,state in zip(calendar,series,states):
            rows.append(dict(fuente=name,mes=month.strftime('%Y-%m'),anio=month.year,
                             mes_numero=month.month,estado=['Fuera de cobertura','Faltante o inválido','Válido'][state],
                             valor=value if state!=0 else np.nan))
        summary.append(dict(Fuente=name,Inicio=start[:7],Fin='2022-12',
                            Validos=int((states==2).sum()),Faltantes=int((states==1).sum()),
                            Fuera_de_cobertura=int((states==0).sum())))
    monthly = pd.DataFrame(rows)
    totals = pd.DataFrame(summary)
    annual = monthly.groupby(['fuente','anio','estado']).size().unstack(fill_value=0).reset_index()
    for name in ['Válido','Faltante o inválido','Fuera de cobertura']:
        if name not in annual: annual[name]=0
    assert totals.Validos.tolist()==[300,504]
    assert totals.Faltantes.tolist()==[0,0]
    assert totals.Fuera_de_cobertura.tolist()==[204,0]
    monthly.to_csv(OUT/'disponibilidad_por_mes.csv',index=False)
    annual.to_csv(OUT/'disponibilidad_por_anio.csv',index=False)
    totals.to_csv(OUT/'resumen_fuentes.csv',index=False)
    colors=['#d9dde1','#de8b36','#34856a']
    months=['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    fig, axis=plt.subplots(figsize=(11,3.7))
    chart=go.Figure()
    state_labels=['Fuera de cobertura','Faltante o inválido','Válido']
    legend_seen=set()
    for n,(matrix,spec) in enumerate(zip(matrices,specs)):
        states=matrix.ravel()
        boundaries=np.r_[0,np.flatnonzero(np.diff(states))+1,len(states)]
        for first,last in zip(boundaries[:-1],boundaries[1:]):
            state=int(states[first]);left=1981+first/12;width=(last-first)/12
            count=int(last-first)
            period=f'{calendar[first]:%Y-%m} a {calendar[last-1]:%Y-%m}'
            label=f'{count} meses '+('válidos' if state==2 else 'fuera de cobertura' if state==0 else 'faltantes')
            axis.barh(n,width,left=left,height=.48,color=colors[state])
            axis.text(left+width/2,n,label,ha='center',va='center',fontsize=10,
                      color='white' if state==2 else '#263744')
            chart.add_trace(go.Bar(y=[spec[0]],x=[width],base=[left],orientation='h',
                width=.48,marker_color=colors[state],name=state_labels[state],
                showlegend=state not in legend_seen,text=[label],textposition='inside',
                customdata=[[period,count]],hovertemplate='%{y}<br>%{customdata[0]}<br>%{customdata[1]} meses<extra>'+state_labels[state]+'</extra>'))
            legend_seen.add(state)
    ticks=[1981,1990,1998,2010,2020,2023]
    ticklabels=['1981','1990','1998','2010','2020','Fin 2022']
    axis.set_yticks([0,1],[s[0] for s in specs]);axis.invert_yaxis()
    axis.set_xlim(1981,2023);axis.set_xticks(ticks,ticklabels)
    axis.set_xlabel('Periodo de estudio');axis.set_title('Cobertura temporal de los datos mensuales')
    axis.axvline(1998,color='#6f7e87',ls='--',lw=.8)
    axis.grid(axis='x',alpha=.18);axis.set_axisbelow(True)
    axis.spines[['top','right','left']].set_visible(False)
    fig.legend(handles=[Patch(color=colors[s],label=state_labels[s]) for s in sorted(legend_seen)],loc='lower center',ncol=len(legend_seen))
    fig.tight_layout(rect=[0,.12,1,1])
    fig.savefig(DOC/'latex'/'figuras'/'disponibilidad_imerg_era5.pdf')
    fig.savefig(OUT/'disponibilidad_imerg_era5.png',dpi=150)
    plt.close(fig)
    chart.update_yaxes(autorange='reversed',categoryorder='array',categoryarray=[s[0] for s in specs])
    chart.update_layout(height=350,barmode='overlay',title='Cobertura temporal de los datos mensuales',
                        xaxis={'range':[1981,2023],'tickvals':ticks,'ticktext':ticklabels},
                        legend={'orientation':'h','y':-.25},margin={'l':160,'r':35,'b':90})
    explanation=('IMERG dispone de 300 meses válidos de enero de 1998 a diciembre de 2022, sin faltantes en ese periodo. '
                 'Los 204 meses de 1981–1997 están fuera de la cobertura utilizada, no son datos perdidos. '
                 'ERA5-Land dispone de los 504 meses de 1981–2022, sin faltantes mensuales. '
                 'Se comprueban fechas mensuales únicas y valores finitos; para precipitación se exige además un valor no negativo. '
                 'Una temperatura negativa en °C no se clasifica como inválida por su signo. '
                 'Esta revisión verifica la presencia y validez del resultado mensual disponible: no demuestra completitud diaria '
                 'de los productos mensuales ni reemplaza la comprobación espacial de IMERG documentada en el punto 1.2. '
                 'Las comparaciones conjuntas conservan solo los 285 meses válidos en todas las variables.')
    html=DOC/'informe_interactivo.html'
    text=html.read_text(encoding='utf-8')
    a,b='<!-- DISPONIBILIDAD_FUENTES_INICIO -->','<!-- DISPONIBILIDAD_FUENTES_FIN -->'
    original=re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    block=a+'<section class="panel" id="disponibilidad-imerg-temperatura"><h2>Disponibilidad mensual de IMERG y temperatura</h2><p>'+explanation+'</p>'
    block+='<div style="overflow:auto">'+totals.to_html(index=False)+'</div>'
    block+=chart.to_html(full_html=False,include_plotlyjs=False,div_id='mapa-disponibilidad-fuentes',config={'responsive':True,'displaylogo':False})
    block+='<details><summary>Conteos por fuente y año</summary><div style="overflow:auto">'+annual.to_html(index=False)+'</div></details></section>'+b
    assert '<footer>' in original
    html.write_text(original.replace('<footer>',block+'<footer>',1),encoding='utf-8')
    tex=explanation.replace('–','--').replace('°',r'$^\circ$')
    source='\\subsubsection*{Disponibilidad mensual de IMERG y temperatura}\n'+tex+'\n'
    source+='\\begin{center}{\\small\n'+totals.to_latex(index=False,escape=True)+'}\\end{center}\n'
    source+='\\begin{figure}[H]\\centering\\includegraphics[width=\\linewidth]{figuras/disponibilidad_imerg_era5.pdf}\\caption{Cobertura temporal mensual. Gris: fuera de cobertura; verde: meses válidos. No hay faltantes dentro de los periodos utilizados. El detalle por año y mes se conserva en los archivos de disponibilidad.}\\end{figure}\n'
    (OUT/'disponibilidad_fuentes.tex').write_text(source,encoding='utf-8')
    print(totals.to_string(index=False))


if __name__=='__main__': main()
