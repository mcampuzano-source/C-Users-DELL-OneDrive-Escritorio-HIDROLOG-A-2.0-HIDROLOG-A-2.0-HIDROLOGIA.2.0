"""Comparaciones visuales del cuarto inciso de 1.3; no modifica las series."""
from pathlib import Path
import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
OUT = DOC / 'imerg_poligono'
FIG = DOC / 'latex' / 'figuras'


def main():
    data = pd.read_csv(OUT / 'meses_comunes_285.csv')
    keys = ['P_CHIRPS_mm', 'P_IMERG_poligono_mm', 'Q_m3_s', 'R_mm', 'Tmedia_ERA5_Land_C']
    labels = ['CHIRPS', 'IMERG', 'Q', 'R', 'Temperatura']
    assert len(data) == 285 and data[keys].notna().all().all()
    # Diferencia estandarizada: admite unidades distintas y el cero convencional de Celsius.
    gap = [(data[k].mean()-data[k].median())/data[k].std(ddof=1) for k in keys]
    p = np.array([5, 10, 25, 50, 75, 90, 95, 100])
    rain = [data[k].quantile(p/100, interpolation='linear').to_numpy() for k in keys[:2]]
    # Diagnóstico de sensibilidad; no se elimina ningún dato de resultados oficiales.
    sensitivity = []
    rows = []
    for k, label in zip(keys, labels):
        s = data[k]
        p95 = s.quantile(.95, interpolation='linear')
        clipped = s.clip(upper=p95)
        delta = (s.mean()-clipped.mean())/s.std(ddof=1)
        sensitivity.append(delta)
        rows.append(dict(variable=label, n=285, media=s.mean(), mediana=s.median(),
                         sd=s.std(ddof=1), diferencia_media_mediana_sd=gap[len(rows)],
                         P95=p95, meses_superiores_P95=int((s>p95).sum()),
                         media_escenario_tope_P95=clipped.mean(), descenso_media_sd=delta))
    pd.DataFrame(rows).to_csv(OUT / 'sensibilidad_extremos_285.csv', index=False)
    titles = ['Centro: media frente a mediana', 'Lluvia: percentiles compartidos', 'Sensibilidad de la media a la cola alta']
    fig, ax = plt.subplots(3, 1, figsize=(10, 12))
    colors = ['#23769b', '#bf5b45', '#206c44', '#6b5291', '#a3344b']
    ax[0].bar(labels, gap, color=colors)
    ax[0].set_ylabel('(Media − mediana) / desviación estándar')
    ax[0].axhline(0, color='black', lw=.7)
    for i,v in enumerate(gap): ax[0].text(i,v+.015,f'{v:.3f}',ha='center')
    for y,name,color in zip(rain,labels,colors): ax[1].plot(p,y,'o-',label=name,color=color)
    ax[1].set(xlabel='Percentil (%) — 100 corresponde al máximo', ylabel='Precipitación (mm/mes)')
    ax[1].legend()
    ax[2].bar(labels,sensitivity,color=colors)
    ax[2].set_ylabel('Descenso hipotético de la media / desviación estándar')
    for i,v in enumerate(sensitivity): ax[2].text(i,v+.003,f'{v:.3f}',ha='center')
    for a,t in zip(ax,titles): a.set_title(t,loc='left');a.grid(axis='y',alpha=.2)
    fig.suptitle('Interpretación de distribuciones: mismos 285 meses comunes, 1998–2022')
    fig.tight_layout(rect=[0,0,1,.97])
    plt.close(fig)
    units = ['mm/mes', 'mm/mes', 'm³/s', 'mm/mes', '°C']
    charts = []
    figure_files = []
    for mode, title, filename in [
        ('centro', titles[0], 'interpretacion_centro'),
        ('cola', titles[2], 'interpretacion_cola_alta')]:
        f, axes = plt.subplots(2, 3, figsize=(12, 7))
        interactive = make_subplots(rows=2, cols=3, subplot_titles=labels, vertical_spacing=.22)
        for i, row in enumerate(rows):
            names = ['Media', 'Mediana'] if mode == 'centro' else ['Media original', 'Tope P95']
            values = [row['media'], row['mediana'] if mode == 'centro' else row['media_escenario_tope_P95']]
            difference = values[0] - values[1]
            precision = 3 if i == 4 else 2
            axis = axes.flat[i]
            axis.bar(names, values, color=[colors[i], '#bccbd3'])
            axis.set(title=labels[i], ylabel=units[i], ylim=(0,max(values)*1.23))
            axis.grid(axis='y', alpha=.2)
            axis.bar_label(axis.containers[0], labels=[f'{v:.{precision}f}' for v in values], padding=3)
            axis.text(.5,.94,f'Diferencia: {difference:.{precision}f} {units[i]}',
                      transform=axis.transAxes,ha='center',fontsize=9)
            interactive.add_trace(go.Bar(x=names,y=values,marker_color=[colors[i], '#bccbd3'],
                text=[f'{v:.{precision}f}' for v in values],textposition='outside',showlegend=False,
                hovertemplate='%{x}: %{y:.3f} '+units[i]+'<extra></extra>'),row=i//3+1,col=i%3+1)
            interactive.update_yaxes(title_text=units[i],range=[0,max(values)*1.23],row=i//3+1,col=i%3+1)
        axes.flat[-1].axis('off')
        subtitle = 'Datos originales: 285 meses comunes' if mode == 'centro' else 'Escenario hipotético: valores mayores que P95 se limitan a P95; datos oficiales intactos'
        f.suptitle(title+'\n'+subtitle,fontsize=12)
        f.tight_layout(rect=[0,0,1,.92])
        f.savefig(FIG / (filename+'.pdf'))
        f.savefig(OUT / (filename+'.png'),dpi=150)
        plt.close(f)
        interactive.update_layout(height=750,title=title+' — 285 meses comunes')
        charts.append((filename,interactive))
        figure_files.append((filename,title))
    chart = go.Figure()
    for y,name,color in zip(rain,labels,colors):
        chart.add_trace(go.Scatter(x=p.tolist(),y=y.tolist(),mode='lines+markers',name=name,line_color=color))
    chart.update_layout(height=550,title=titles[1]+' — 285 meses comunes',
                        xaxis_title='Percentil (%) — 100 corresponde al máximo',yaxis_title='Precipitación (mm/mes)')
    f, axis = plt.subplots(figsize=(10,5))
    for y,name,color in zip(rain,labels,colors): axis.plot(p,y,'o-',label=name,color=color)
    axis.set(title=titles[1]+' — 285 meses comunes',xlabel='Percentil (%) — 100 corresponde al máximo',ylabel='Precipitación (mm/mes)')
    axis.legend();axis.grid(alpha=.2);f.tight_layout()
    f.savefig(FIG / 'interpretacion_percentiles.pdf');f.savefig(OUT / 'interpretacion_percentiles.png',dpi=150);plt.close(f)
    charts.insert(1,('interpretacion_percentiles',chart))
    figure_files.insert(1,('interpretacion_percentiles',titles[1]))
    explanation = ('La primera figura compara media y mediana con sus valores reales y unidades propias, en paneles separados: '
                   'Q y R presentan mayor separación, mientras lluvia y temperatura tienen centros próximos. '
                   'La segunda compara los mismos percentiles de ambas precipitaciones; permite localizar las diferencias '
                   'en el centro y las colas, sin confundir percentiles con fechas. La tercera muestra un diagnóstico '
                   'hipotético: se limita cada valor superior a P95 a ese umbral y se mide cuánto bajaría la media '
                   'en las unidades de cada variable. Los valores y las diferencias se indican explícitamente; '
                   'cada panel usa su propia escala, por lo que no deben compararse alturas entre variables. '
                   'La comparación evidencia sensibilidad a la cola alta, '
                   'no errores ni una corrección recomendada. Los datos, gráficos y estadísticos oficiales conservan '
                   'todos los valores originales. La proximidad de media y mediana no demuestra normalidad. '
                   'Las distribuciones mezclan meses calendario; no representan la climatología del punto 1.5.')
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    a,b = '<!-- INTERPRETACION_GRAFICAS_INICIO -->','<!-- INTERPRETACION_GRAFICAS_FIN -->'
    original = re.sub(re.escape(a)+'.*?'+re.escape(b),'',text,flags=re.S)
    block = a+'<div id="interpretacion-distribuciones"><h3>Interpretación visual: condición típica, extremos y fuentes</h3><p>'+explanation+'</p>'
    for name, plot in charts:
        block += plot.to_html(full_html=False,include_plotlyjs=False,div_id=name,config={'responsive':True,'displaylogo':False})
    block += '</div>'+b
    start=original.index('<section class="panel" id="imerg-poligono-estadisticos">')
    end=original.index('</section>',start)
    updated=original[:end]+block+original[end:]
    assert re.sub(re.escape(a)+'.*?'+re.escape(b),'',updated,flags=re.S)==original
    html.write_text(updated,encoding='utf-8')
    tex = explanation.replace('−','-')
    tex_source = '\\subsubsection*{Interpretación visual: condición típica, extremos y fuentes}\n'+tex+'\n'
    for name,title in figure_files:
        tex_source += '\\begin{figure}[H]\\centering\\includegraphics[width=\\linewidth]{figuras/'+name+'.pdf}\\caption{'+title+'. Mismos 285 meses comunes; paneles con unidades propias.'+(' El tope en P95 es solo un escenario hipotético, no una corrección de datos.' if name.endswith('cola_alta') else '')+'}\\end{figure}\n'
    (OUT / 'interpretacion_graficas.tex').write_text(tex_source,encoding='utf-8')
    print(pd.DataFrame(rows).to_string(index=False))


if __name__=='__main__': main()
