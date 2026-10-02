"""Descripción global y por año de valores mensuales válidos de P y Q."""
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'
LATEX=DOC/'latex'
data=pd.read_csv(DOC/'datos_graficados.csv',parse_dates=['mes']).set_index('mes')
rows=[]
for period,block in [('1981–2022',data)]+[(str(year),block) for year,block in data.groupby(data.index.year)]:
    for var,name,unit in [('P_mm','Precipitación','mm/mes'),('Q_m3_s','Caudal','m³/s')]:
        values=block[var].dropna()
        rows.append({'Periodo':period,'Variable':name,'Unidad':unit,'Meses válidos':len(values),'Media':values.mean(),'Mediana':values.median(),'Desviación estándar':values.std(ddof=1),'Mínimo':values.min(),'Máximo':values.max()})
table=pd.DataFrame(rows)
overall=table.iloc[:2]; annual=table.iloc[2:]
assert len(annual)==84
assert overall['Meses válidos'].eq(485).all()
assert annual.groupby('Variable')['Meses válidos'].sum().eq(485).all()
table.to_csv(DOC/'estadisticas_globales_y_por_ano.csv',index=False,encoding='utf-8-sig')
with pd.ExcelWriter(DOC/'Estadisticas_por_ano.xlsx',engine='openpyxl') as writer:
    overall.to_excel(writer,sheet_name='Periodo completo',index=False)
    annual.to_excel(writer,sheet_name='Por año',index=False)
    for ws in writer.book:
        ws.freeze_panes='D2'; ws.auto_filter.ref=ws.dimensions
        for cell in ws[1]:
            ws.column_dimensions[cell.column_letter].width=23
        for row in ws.iter_rows(min_row=2,min_col=5):
            for cell in row:
                cell.number_format='0.00'

description='''<p>Los datos originales son diarios y se agregaron a escala mensual. El periodo analizado va de <b>enero de 1981 a diciembre de 2022 (42 años)</b>. Las estadísticas siguientes describen los meses válidos: precipitación acumulada mensual (mm/mes) y caudal medio mensual (m³/s). No son estadísticas de los valores diarios ni de totales anuales.</p><p>La tabla global reúne 485 meses por variable. El desglose por año indica cuántos meses se conservaron; cuando son menos de 12, las cifras describen solo los meses disponibles y su comparación entre años puede verse afectada por las estaciones del año que faltan. No se rellenan datos.</p><p>Se usa desviación estándar muestral (<code>ddof=1</code>) y mediana con interpolación lineal. La media global es una media aritmética de meses válidos, no una media de las medias anuales ni una media de caudal ponderada por el número de días. Mínimo y máximo son extremos mensuales.</p>'''
section='''<!-- ESTADISTICAS_ANUALES_INICIO --><section class="panel" id="estadisticas-anuales"><h2>3. Periodo de datos y estadística descriptiva</h2>'''+description+'<h3>Periodo completo: 1981–2022</h3><div style="overflow:auto">'+overall.to_html(index=False,border=0,classes='tabla-estadistica',float_format=lambda v:f'{v:.2f}')+'</div><h3>Descripción por año</h3><label>Año o variable: <input id="buscar-estadisticas" placeholder="Ejemplo: 1992 o Caudal" oninput="document.querySelectorAll(\'#tabla-estadisticas-anuales tbody tr\').forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase()))" style="padding:8px;margin:10px"></label><div style="overflow:auto;max-height:650px">'+annual.to_html(index=False,border=0,table_id='tabla-estadisticas-anuales',classes='tabla-estadistica',float_format=lambda v:f'{v:.2f}')+'''</div><style>.tabla-estadistica{border-collapse:collapse;width:100%}.tabla-estadistica th,.tabla-estadistica td{padding:8px;border-bottom:1px solid #d8e1e7;text-align:left;white-space:nowrap}.tabla-estadistica th{background:#edf3f5;position:sticky;top:0}</style><p>Una mayor desviación estándar indica mayor dispersión de los meses observados, pero no es una medida directa del error de medición. La media de caudal supera su mediana en el periodo completo, lo que refleja la influencia de meses de caudal alto.</p></section><!-- ESTADISTICAS_ANUALES_FIN -->'''
path=DOC/'informe_interactivo.html'; html=path.read_text(encoding='utf-8')
start='<!-- ESTADISTICAS_ANUALES_INICIO -->'; end='<!-- ESTADISTICAS_ANUALES_FIN -->'
if start in html:
    left,rest=html.split(start,1); _,right=rest.split(end,1); html=left+right
html=html.replace('<footer>',section+'<footer>',1).replace('Pasos 1–2','Pasos 1–3')
path.write_text(html,encoding='utf-8')

def texrow(row):
    name='P' if row['Variable']=='Precipitación' else 'Q'
    nums=[f'{row[c]:.2f}'.replace('.',',') for c in ['Media','Mediana','Desviación estándar','Mínimo','Máximo']]
    return ' & '.join([row['Periodo'].replace('–','--'),name,str(row['Meses válidos'])]+nums)+r' \\'
header=r'Periodo & Variable & Meses & Media & Mediana & Desv. est. & Mínimo & Máximo \\'
tex=r'''\section{Periodo de datos y estadística descriptiva}
Los registros originales son diarios y se agregaron a escala mensual. El periodo
comprende enero de 1981 a diciembre de 2022 (42 años). Se describen los valores
mensuales válidos de precipitación acumulada y caudal medio, no los registros
diarios ni los totales anuales.

En las tablas, P corresponde a precipitación en mm/mes y Q a caudal en m$^3$/s.
Se usa desviación estándar muestral ($n-1$ en el denominador), mediana con
interpolación lineal y media aritmética de meses válidos. La media global no es
la media de medias anuales ni un promedio ponderado por la duración del mes.

\subsection{Periodo completo: 1981--2022}
\begin{center}\small
\begin{tabular}{llrrrrrr}\hline
'''+header+'\n'+r'\hline'+'\n'+'\n'.join(texrow(row) for _,row in overall.iterrows())+r'''
\hline\end{tabular}\end{center}
Los mínimos y máximos son extremos de valores mensuales. En Q, la media superior
a la mediana refleja la influencia de meses de caudal alto. La desviación estándar
describe dispersión, no error de medición.

\subsection{Descripción por año}
Se indica el número de meses válidos en cada año. Si es menor de 12, las cifras
describen únicamente los meses disponibles. Los años incompletos no representan
todo el ciclo anual y su comparación puede verse afectada por los meses ausentes.
No se rellenaron datos. Todos los valores conservan las unidades mensuales indicadas.

\begingroup\small
\begin{longtable}{llrrrrrr}
\caption{Estadística por año de las series mensuales válidas. P: mm/mes; Q: m$^3$/s.}\\
\hline
'''+header+r'''
\hline\endfirsthead
\multicolumn{8}{l}{Continuación: estadística de valores mensuales por año}\\
\hline
'''+header+r'''
\hline\endhead
\hline\multicolumn{8}{r}{Continúa en la siguiente página}\\\endfoot
\hline\endlastfoot
'''+ '\n'.join(texrow(row) for _,row in annual.iterrows())+r'''
\end{longtable}\endgroup
'''
(LATEX/'secciones'/'03_estadistica_por_ano.tex').write_text(tex,encoding='utf-8')
main=LATEX/'informe.tex'; text=main.read_text(encoding='utf-8')
if r'\usepackage{longtable}' not in text:
    text=text.replace(r'\usepackage{float}',r'\usepackage{float}'+'\n'+r'\usepackage{longtable}')
if r'\input{secciones/03_estadistica_por_ano}' not in text:
    text=text.replace(r'\end{document}',r'\clearpage'+'\n'+r'\input{secciones/03_estadistica_por_ano}'+'\n'+r'\end{document}')
text=text.replace('Pasos 1 y 2','Pasos 1 a 3')
main.write_text(text,encoding='utf-8')
print('Agregadas 2 filas globales y 84 filas por año: 42 años x 2 variables.')
