"""Ordena los informes existentes sin recalcular datos ni generar figuras.

Ejecutar después de regenerar los documentos con los scripts anteriores.
Las fuentes originales por sección se mantienen como entradas sin modificar.
"""
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'
LATEX = DOC / 'latex'


def lower_headings(text):
    text = re.sub(r'\\subsection\*?\{', lambda _: r'\subsubsection*{', text)
    return re.sub(r'\\section\*?\{', lambda _: r'\subsubsection*{', text)


def organize_pdf():
    sources = {p.stem: p.read_text(encoding='utf-8') for p in (LATEX / 'secciones').glob('*.tex')}
    temperature = sources['05_temperatura_dispersion_mapas']
    split_disp = temperature.index(r'\section{Diagramas de dispersión')
    split_geo = temperature.index(r'\subsection{Contexto geográfico')
    temp, dispersion, maps = temperature[:split_disp], temperature[split_disp:split_geo], temperature[split_geo:]
    relations = sources['09_dispersiones_analisis']
    boundaries = [m.start() for m in re.finditer(r'\\subsection\{', relations)]
    parts = [relations[a:b] for a, b in zip(boundaries, boundaries[1:] + [len(relations)])]
    assert len(parts) == 5
    cycle_end = parts[0].index('\n\n')
    imerg_cycle, imerg_reading = parts[0][:cycle_end], parts[0][cycle_end:]
    preamble = (LATEX / 'informe.tex').read_text(encoding='utf-8').split(r'\begin{document}')[0]
    if r'\usepackage{booktabs}' not in preamble:
        preamble += '\\usepackage{booktabs}\n'
    new_folder = DOC / 'imerg_poligono'
    new12 = (new_folder / 'apartado_1_2.tex').read_text(encoding='utf-8') if (new_folder / 'apartado_1_2.tex').exists() else ''
    new13 = (new_folder / 'apartado_1_3.tex').read_text(encoding='utf-8') if (new_folder / 'apartado_1_3.tex').exists() else ''
    def block(title, content):
        return '\n' + title + '\n' + lower_headings(content) + '\n'
    content = preamble + r'''\begin{document}
\begin{center}
{\Large\bfseries Cuenca del río La Vieja}\\[3pt]
{\large Exploración hidroclimática mensual}\\[5pt]
Curso de Hidrología -- Tarea 1\\
{\small Documento en construcción -- Orden de la guía}
\end{center}
\tableofcontents
\clearpage
\section*{Introducción}
Pendiente de redacción final.
\section*{Metodología}
Los procedimientos existentes se conservan junto a cada análisis; la metodología integrada está pendiente de redacción final.
\section*{Resultados y discusión física}
'''
    content += block(r'\section*{Contexto geográfico de la cuenca}', maps)
    content += '\\clearpage\n\\section{Series mensuales: exploración y validación}\n'
    content += block(r'\subsection{Graficar las series de caudal y precipitación}', sources['01_series_mensuales'] + temp + parts[1])
    content += block(r'\subsection{Incorporar precipitación IMERG para la misma cuenca}', new12 + (r'\subsubsection*{Antecedentes conservados: IMERG promedio de caja}' if new12 else '') + imerg_reading)
    content += block(r'\subsection{Describir la distribución de los datos mensuales}', new13 + (r'\subsubsection*{Antecedentes conservados: fuentes y muestras anteriores}' if new13 else '') + sources['03_estadistica_por_ano'] + sources['06_histogramas_estadisticos'] + parts[2])
    content += block(r'\subsection{Usar la exploración como control de calidad}', sources['02_control_faltantes'])
    content += block(r'\subsection{Climatología, variabilidad y explicación física}', imerg_cycle)
    content += 'Apartado pendiente de completar según la guía; esta reorganización no incorpora resultados nuevos.\n'
    for title in ['1.5.a. Construir la climatología de doce meses', '1.5.b. Describir y contrastar el ciclo anual', '1.5.c. Explicar los procesos regionales y de la cuenca']:
        content += '\\subsubsection*{' + title + '}\nPendiente de completar e integrar.\n'
    content += '\\clearpage\n\\section{Relaciones entre series y modelos estadísticos}\n'
    content += block(r'\subsection{Diagramas de dispersión e interpretación}', parts[3] + dispersion + parts[4])
    for title in ['¿Se pueden construir modelos útiles?', 'Evaluar fuera del periodo de ajuste']:
        content += '\\subsection{' + title + '}\nPendiente de desarrollar.\n'
    content += '\\clearpage\n\\section{Tendencias hidroclimáticas y sus posibles causas}\n'
    for title in ['Temperatura y periodos de análisis', 'Series originales, anomalías y anomalías estandarizadas', 'Dos escalas de evaluación temporal', 'Métodos y comparación de resultados', 'Incertidumbre, robustez y presentación', '¿A qué podrían deberse los cambios?']:
        content += '\\subsection{' + title + '}\n'
        if title == 'Métodos y comparación de resultados':
            content += lower_headings(sources['08_tendencias'])
        else:
            content += 'Pendiente de completar e integrar; los resultados existentes se conservan en el apartado 3.4 y las series en el punto 1.\n'
    for title, subs in [('Análisis de frecuencias mediante Fourier', ['Preparar las series y documentar el cálculo', 'Construir e interpretar los espectros']), ('Mapas de correlación con el clima global', ['Seleccionar los campos climáticos', 'Definir y calcular los mapas mensuales', 'Robustez y presentación de los patrones', 'Interpretación física e integración'])]:
        content += '\\clearpage\n\\section{' + title + '}\n'
        for sub in subs:
            content += '\\subsection{' + sub + '}\nPendiente de desarrollar.\n'
    content += '\\section*{Conclusiones}\nPendiente de síntesis final.\n'
    content += block(r'\section*{Procedencia, alcance y reproducibilidad}', sources['04_procedencia_alcance'])
    content += '\\section*{Uso de IA}\nLa declaración existente se conserva en el apartado anterior; falta completar la declaración final del grupo.\n'
    content += '\\section*{Referencias y anexos}\nLas referencias y fuentes existentes se conservan junto a sus análisis; falta consolidar el listado final.\n'
    content += '\\end{document}\n'
    original_used = ''.join(sources[name] for name in ['01_series_mensuales', '02_control_faltantes', '03_estadistica_por_ano', '05_temperatura_dispersion_mapas', '06_histogramas_estadisticos', '09_dispersiones_analisis', '08_tendencias', '04_procedencia_alcance'])
    figures = lambda t: sorted(re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}', t))
    assert figures(content) == figures(original_used + new12 + new13), 'Se modificó el inventario de figuras'
    def bodies(text):
        text = re.sub(r'\\(?:subsubsection|subsection|section)\*?\{[^\n]*?\}', '', text)
        return re.sub(r'\s+', '', text)
    final_body = bodies(content)
    for chunk in re.split(r'\\(?:section|subsection)\*?\{[^\n]*?\}|\n\s*\n', original_used):
        if chunk.strip():
            assert bodies(chunk) in final_body, 'Se omitió un bloque de contenido original'
    (LATEX / 'informe_ordenado.tex').write_text(content, encoding='utf-8')
    subprocess.run([str(ROOT / 'herramientas' / 'tectonic' / 'tectonic.exe'), 'informe_ordenado.tex', '--keep-logs'], cwd=LATEX, check=True)
    shutil.copyfile(LATEX / 'informe_ordenado.pdf', DOC / 'informe_actualizado.pdf')


LAYOUT_SCRIPT = r'''<!-- ORDEN_GUIA_INICIO -->
<script>
/* Solo mueve nodos existentes: no altera los datos ni el diseño de las gráficas. */
(function(){
function ordenar(){
 const main=document.querySelector('main'), footer=main.querySelector('footer');
 if(document.getElementById('orden-guia'))return;
 const root=document.createElement('div');root.id='orden-guia';main.insertBefore(root,footer);
 const nav=document.createElement('nav');nav.className='panel';
 nav.innerHTML='<b>Orden de la guía</b><p><a href="#guia-contexto">Cuenca y mapas</a> · <a href="#guia-punto-1">Punto 1</a> · <a href="#guia-punto-2">Punto 2</a> · <a href="#guia-punto-3">Punto 3</a> · <a href="#guia-punto-4">Punto 4</a> · <a href="#guia-punto-5">Punto 5</a></p>';
 root.appendChild(nav);
 function grupo(id,title){const el=document.createElement('div');el.id=id;const h=document.createElement('h2');h.textContent=title;el.appendChild(h);root.appendChild(el);return el;}
 function sub(parent,id,title){const el=document.createElement('div');el.id=id;const h=document.createElement('h3');h.textContent=title;el.appendChild(h);parent.appendChild(el);return el;}
 function mover(parent,el,title){if(!el)return;parent.appendChild(el);if(title){const h=el.querySelector('h2');if(h)h.textContent=title;}}
 function pendiente(parent,text){const p=document.createElement('p');p.textContent=text||'Pendiente de completar e integrar.';parent.appendChild(p);}
 pendiente(grupo('guia-introduccion','Introducción'),'Pendiente de redacción final.');
 pendiente(grupo('guia-metodologia','Metodología'),'Los procedimientos existentes se conservan junto a cada análisis; la metodología integrada está pendiente de redacción final.');
 grupo('guia-resultados','Resultados y discusión física');
 const contexto=grupo('guia-contexto','Contexto geográfico de la cuenca');
 mover(contexto,document.getElementById('mapas-geograficos'));
 const p1=grupo('guia-punto-1','Punto 1. Series mensuales: exploración y validación');
 const s11=sub(p1,'guia-1-1','1.1. Graficar las series de caudal y precipitación');
 const series=document.getElementById('series-mensuales').closest('section');
 mover(s11,series,'Series cronológicas interactivas: CHIRPS y caudal Q');
 for(const section of Array.from(main.querySelectorAll('section.panel'))){const h=section.querySelector('h2');if(h&&['Cómo se construyeron las series','Meses extremos y contraste cronológico'].includes(h.textContent))mover(s11,section);}
 mover(s11,document.getElementById('agregacion-mensual-imerg'));
 mover(s11,document.getElementById('temperatura-era5'));
 const s12=sub(p1,'guia-1-2','1.2. Incorporar precipitación IMERG para la misma cuenca');
 mover(s12,document.getElementById('imerg-poligono-metodo'));
 if(document.getElementById('imerg-poligono-metodo'))pendiente(s12,'Antecedentes conservados: las gráficas y explicaciones siguientes de IMERG corresponden al promedio Giovanni de caja anterior. Sus resultados no se sustituyen ni se mezclan con el promedio de polígono presentado arriba.');
 mover(s12,document.getElementById('imerg-caudal-interactivo'));
 mover(s12,document.getElementById('lectura-temporal-imerg'));
 const s13=sub(p1,'guia-1-3','1.3. Describir la distribución de los datos mensuales');
 mover(s13,document.getElementById('imerg-poligono-estadisticos'));
 if(document.getElementById('imerg-poligono-estadisticos'))pendiente(s13,'Antecedentes conservados: los cuadros siguientes mantienen los productos y periodos de las versiones anteriores, incluida IMERG de caja y temperatura estimada MSWX. La comparación actual de polígono y ERA5-Land se presenta arriba.');
 mover(s13,document.getElementById('estadisticas-anuales'),'Periodo de datos y estadística descriptiva');
 mover(s13,document.getElementById('histogramas'),'Histogramas y estadísticos completos');
 const s14=sub(p1,'guia-1-4','1.4. Usar la exploración como control de calidad');
 mover(s14,document.getElementById('faltantes'),'Control de datos faltantes');
 const s15=sub(p1,'guia-1-5','1.5. Climatología, variabilidad y explicación física');
 const pending=document.createElement('p');pending.textContent='Apartado pendiente de completar según la guía; esta reorganización no incorpora resultados nuevos.';s15.appendChild(pending);
 for(const [id,title] of [['guia-1-5-a','1.5.a. Construir la climatología de doce meses'],['guia-1-5-b','1.5.b. Describir y contrastar el ciclo anual'],['guia-1-5-c','1.5.c. Explicar los procesos regionales y de la cuenca']])pendiente(sub(s15,id,title));
 const p2=grupo('guia-punto-2','Punto 2. Relaciones entre series y modelos estadísticos');
 const s21=sub(p2,'guia-2-1','2.1. Diagramas de dispersión e interpretación');
 mover(s21,document.getElementById('dispersiones-imerg'));
 mover(s21,document.getElementById('analisis-dispersion'),'Análisis paralelo: CHIRPS–Q');
 pendiente(sub(p2,'guia-2-2','2.2. ¿Se pueden construir modelos útiles?'));
 pendiente(sub(p2,'guia-2-3','2.3. Evaluar fuera del periodo de ajuste'));
 const p3=grupo('guia-punto-3','Punto 3. Tendencias hidroclimáticas y sus posibles causas');
 ['Temperatura y periodos de análisis','Series originales, anomalías y anomalías estandarizadas','Dos escalas de evaluación temporal','Métodos y comparación de resultados','Incertidumbre, robustez y presentación','¿A qué podrían deberse los cambios?'].forEach((title,i)=>{const el=sub(p3,'guia-3-'+(i+1),'3.'+(i+1)+'. '+title);if(i===3)mover(el,document.getElementById('tendencias'),'Tendencias temporales');else pendiente(el,'Pendiente de completar e integrar; los resultados existentes se conservan en el apartado 3.4 y las series en el punto 1.');});
 for(const [n,title,titles] of [[4,'Análisis de frecuencias mediante Fourier',['Preparar las series y documentar el cálculo','Construir e interpretar los espectros']],[5,'Mapas de correlación con el clima global',['Seleccionar los campos climáticos','Definir y calcular los mapas mensuales','Robustez y presentación de los patrones','Interpretación física e integración']]]){const el=grupo('guia-punto-'+n,'Punto '+n+'. '+title);titles.forEach((t,i)=>pendiente(sub(el,'guia-'+n+'-'+(i+1),n+'.'+(i+1)+'. '+t),'Pendiente de desarrollar.'));}
 pendiente(grupo('guia-conclusiones','Conclusiones'),'Pendiente de síntesis final.');
 const fin=grupo('guia-procedencia','Procedencia, alcance y reproducibilidad');mover(fin,document.getElementById('procedencia-alcance'));
 pendiente(grupo('guia-ia','Uso de IA'),'La declaración existente se conserva en el apartado anterior; falta completar la declaración final del grupo.');
 pendiente(grupo('guia-referencias','Referencias y anexos'),'Las referencias y fuentes existentes se conservan junto a sus análisis; falta consolidar el listado final.');
 if(window.Plotly)document.querySelectorAll('.js-plotly-plot').forEach(g=>Plotly.Plots.resize(g));
}
if(document.readyState==='complete')setTimeout(ordenar,800);else window.addEventListener('load',()=>setTimeout(ordenar,800));
})();
</script>
<!-- ORDEN_GUIA_FIN -->'''


def organize_html():
    path = DOC / 'informe_interactivo.html'
    text = path.read_text(encoding='utf-8')
    text = re.sub(r'<!-- ORDEN_GUIA_INICIO -->.*?<!-- ORDEN_GUIA_FIN -->', '', text, flags=re.S)
    assert '</body>' in text
    path.write_text(text.replace('</body>', LAYOUT_SCRIPT + '\n</body>'), encoding='utf-8')


if __name__ == '__main__':
    organize_html()
    organize_pdf()
    print('HTML y PDF ordenados; datos y figuras originales conservados.')
