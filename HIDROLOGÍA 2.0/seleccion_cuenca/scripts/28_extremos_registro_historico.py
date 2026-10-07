"""Contrasta los extremos históricos anteriores a IMERG, sin modificar series."""
from pathlib import Path
import re
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from plotly.subplots import make_subplots
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
OUT = DOC / 'imerg_poligono'


def main():
    data = pd.read_csv(OUT / 'series_alineadas.csv', parse_dates=['mes']).set_index('mes')
    stats = pd.read_csv(OUT / 'estadisticos_registros.csv')
    selected = stats.loc[stats.mes_minimo < '1998-01', ['variable','unidad','mes_minimo','minimo']]
    selected = selected.rename(columns={'variable':'Variable','unidad':'Unidad','mes_minimo':'Mes mínimo','minimo':'Mínimo'})
    keys = ['P_CHIRPS_mm','Q_m3_s','Tmedia_ERA5_Land_C']
    labels = ['CHIRPS (mm/mes)','Caudal Q (m³/s)','ERA5-Land Tmedia (°C)']
    periods = [('1982-06','1982-10','1982-08'),('1992-05','1992-09','1992-07'),('1983-11','1984-03','1984-01')]
    fig, axes = plt.subplots(3,3,figsize=(12,9))
    chart = make_subplots(rows=3,cols=3,subplot_titles=[f'{month}: {label}' for _,_,month in periods for label in labels],vertical_spacing=.12)
    colors = ['#23769b','#206c44','#a3344b']
    for r,(start,end,month) in enumerate(periods):
        frame = data.loc[start:end]
        for c,(key,label) in enumerate(zip(keys,labels)):
            axes[r,c].plot(frame.index,frame[key],'o-',color=colors[c])
            axes[r,c].axvline(pd.Timestamp(month+'-01'),color='#bf5b45',ls='--',lw=1)
            axes[r,c].set_title(month+': '+label,fontsize=10)
            axes[r,c].set_xticks(frame.index,frame.index.strftime('%Y-%m'),rotation=45,ha='right')
            axes[r,c].grid(alpha=.2)
            chart.add_trace(go.Scatter(x=frame.index.strftime('%Y-%m-%d').tolist(),
                y=[float(v) if pd.notna(v) else None for v in frame[key]],mode='lines+markers',connectgaps=False,
                name=label,line_color=colors[c],showlegend=False),row=r+1,col=c+1)
            chart.add_vline(x=pd.Timestamp(month+'-01').timestamp()*1000,line_dash='dash',line_color='#bf5b45',row=r+1,col=c+1)
    fig.suptitle('Extremos del registro completo: mes señalado y meses vecinos\nSin comparación con IMERG; cortes = datos ausentes',fontsize=12)
    fig.tight_layout(rect=[0,0,1,.94])
    fig.savefig(DOC / 'latex' / 'figuras' / 'extremos_historicos.pdf')
    fig.savefig(OUT / 'extremos_historicos.png',dpi=150)
    plt.close(fig)
    chart.update_layout(height=1000,title='Extremos históricos anteriores a 1998: mes señalado y vecinos')
    paragraphs = [
        'Este contraste utiliza el registro completo por fuente, separado de los 285 meses comunes con IMERG. '
        'Se revisan agosto de 1982, julio de 1992 y enero de 1984 porque contienen los mínimos históricos que no aparecen '
        'en la figura de 1998–2022. Son datos válidos anteriores a la cobertura IMERG utilizada, no meses descartados por ese motivo. '
        'Los máximos de CHIRPS, Q, R y temperatura están dentro del periodo ya analizado; el máximo IMERG de noviembre de 2008 '
        'se mantiene aparte por ausencia de CHIRPS y Q.',
        'Agosto de 1982: CHIRPS alcanza 24,89 mm/mes, tras 87,29 en junio y 53,49 en julio. '
        'Q desciende de 77,22 a 45,62 y 29,20 m³/s; R es 27,96 mm/mes en agosto. '
        'En septiembre aumenta la lluvia a 168,27 mm/mes, pero Q permanece bajo (31,70 m³/s), '
        'y en octubre sube a 66,39 m³/s. Es una secuencia plausible de condiciones secas y recuperación posterior; '
        'el mínimo de lluvia no constituye por sí solo un problema de datos.',
        'Julio de 1992: Q y R alcanzan sus mínimos históricos (18,37 m³/s y 17,59 mm/mes). '
        'CHIRPS registra 75,46 mm/mes, después de 80,03 en junio; Q ya era bajo en mayo y junio '
        '(28,16 y 28,38 m³/s). La persistencia de caudal bajo es compatible con almacenamiento reducido, '
        'pero agosto y septiembre tienen datos ausentes de CHIRPS, Q y R: no puede comprobarse la evolución posterior '
        'con esas series ni rellenarse el vacío con cero.',
        'Enero de 1984: ERA5-Land alcanza su temperatura mínima (14,84 °C), con valores próximos en diciembre '
        '(15,12 °C) y febrero (15,05 °C). CHIRPS permanece entre 190,87 y 236,26 mm/mes en esos tres meses '
        'y Q entre 98,77 y 127,13 m³/s. El mínimo está integrado en una secuencia de temperaturas bajas y lluvia '
        'apreciable, sin un salto aislado evidente. Es plausible, pero no prueba causalidad ni exactitud del reanálisis. '
        'En conjunto, no se identifican errores confirmados: se conservan todos los valores y se reconoce la limitación '
        'de los faltantes de 1992. R deriva de Q, por lo que su coincidencia no constituye evidencia independiente.'
    ]
    table_html = '<div style="overflow:auto">'+selected.to_html(index=False,float_format=lambda v:f'{v:.2f}')+'</div>'
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    a,b='<!-- EXTREMOS_HISTORICOS_INICIO -->','<!-- EXTREMOS_HISTORICOS_FIN -->'
    original = re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    block = a+'<div id="extremos-historicos"><h3>Extremos del registro completo anteriores a 1998</h3>'+table_html
    block += ''.join('<p>'+p+'</p>' for p in paragraphs)
    block += chart.to_html(full_html=False,include_plotlyjs=False,div_id='extremos-historicos-cronologias',config={'responsive':True,'displaylogo':False})+'</div>'+b
    start = original.index('<section class="panel" id="imerg-poligono-estadisticos">')
    end = original.index('</section>',start)
    updated = original[:end]+block+original[end:]
    assert re.sub(re.escape(a)+'.*?'+re.escape(b),'',updated,flags=re.S)==original
    html.write_text(updated,encoding='utf-8')
    path = OUT / 'contraste_extremos.tex'
    text = path.read_text(encoding='utf-8')
    ta,tb='% EXTREMOS_HISTORICOS_INICIO','% EXTREMOS_HISTORICOS_FIN'
    original = re.sub(re.escape(ta)+'.*?'+re.escape(tb),'',text,flags=re.S)
    tex = '\n'+ta+'\n\\subsubsection*{Extremos del registro completo anteriores a 1998}\n'
    tex += '\\begin{center}{\\small\n'+selected.to_latex(index=False,escape=True,float_format='%.2f')+'}\\end{center}\n'
    tex += '\n\n'.join(p.replace('³',r'$^3$').replace('°',r'$^\circ$').replace('–','--') for p in paragraphs)
    tex += '\n\\begin{figure}[H]\\centering\\includegraphics[width=\\linewidth]{figuras/extremos_historicos.pdf}\\caption{Extremos históricos y meses vecinos. La línea discontinua señala el mes extremo; los cortes conservan las ausencias. R se detalla en el texto y la tabla.}\\end{figure}\n'+tb+'\n'
    path.write_text(original+tex,encoding='utf-8')
    print(selected.to_string(index=False))


if __name__=='__main__': main()
