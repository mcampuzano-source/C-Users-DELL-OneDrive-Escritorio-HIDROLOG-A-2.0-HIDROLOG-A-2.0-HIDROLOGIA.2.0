"""Sección final de procedencia y alcance en LaTeX y HTML autocontenido."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'la_vieja'/'documentos'
LATEX=DOC/'latex'
section='''<!-- PROCEDENCIA_INICIO --><section class="panel" id="procedencia-alcance"><h2>Procedencia y alcance</h2>
<h3>Procedencia de los datos</h3>
<p>La fuente es <b>CAMELS-COL</b>, depósito del 26 de febrero de 2026, DOI <a href="https://doi.org/10.5281/zenodo.18794895">10.5281/zenodo.18794895</a>, consultado el 21 de septiembre de 2026. Se utiliza el archivo <code>Hydromet_data_26127040.txt</code>, contenido en <code>04_CAMELS_COL_Hydrometeorological_data.zip</code>, para la cuenca del río La Vieja hasta la estación Cartago, código IDEAM 26127040.</p>
<ul><li><b>Precipitación:</b> CHIRPS v2, valores diarios promediados sobre la cuenca por los autores de CAMELS-COL, en mm/día. Es un producto combinado, no una medición directa de un único pluviómetro.</li><li><b>Caudal:</b> caudal diario reportado como observado en la estación hidrométrica IDEAM, distribuido mediante CAMELS-COL, en m³/s. No se descargaron aforos originales directamente del IDEAM.</li><li><b>Área y delimitación:</b> atributos y polígono CAMELS-COL. Área reportada: 2.797,19 km². El nombre y la ubicación de la estación se contrastaron con el catálogo IDEAM.</li><li><b>Temperatura:</b> el archivo incluye Tmin y Tmax de MSWX; se grafican sus medias mensuales y una Tmedia estimada mediante (Tmin + Tmax)/2; no es una media horaria observada.</li></ul>
<h3>Alcance temporal y procesamiento</h3>
<p>Se analiza enero de 1981 a diciembre de 2022 (42 años). Se reconstruyó el calendario diario y se conservaron solo meses con el 100 % de días válidos: 485 meses de 504. P mensual es la suma de P diaria y Q mensual es la media de Q diaria. No se rellenaron faltantes, no se prorratearon sumas ni se eliminaron extremos por su magnitud.</p>
<p>Las estadísticas globales y por año describen valores mensuales válidos; mínimo y máximo no son extremos instantáneos ni diarios. La desviación estándar es muestral. Los años con menos de doce meses describen únicamente su muestra disponible.</p>
<h3>Limitaciones y trabajo pendiente</h3>
<p>Este documento es una exploración descriptiva inicial. La cartografía de relieve utiliza Copernicus GLO-30, documentado en la sección de mapas. Las gráficas no prueban tendencias, causalidad ni capacidad predictiva. No se ha certificado la homogeneidad del registro, la ausencia de reconstrucciones previas o el efecto de extracciones y regulación. El archivo diario no ofrece banderas por observación para resolver esas cuestiones.</p>
<p><b>IMERG aún no está incorporado:</b> se verificó cobertura en catálogo, pero no se descargaron ni validaron valores sobre la cuenca. También están pendientes una temperatura media de fuente directa y la evaluación de los registros individuales de estaciones de lluvia. El conteo de estaciones del catálogo no demuestra continuidad de sus series ni significa que se hayan utilizado como datos de entrada.</p>
<h3>Reproducibilidad y apoyo de IA</h3>
<p>Los scripts numerados se conservan en <code>seleccion_cuenca/scripts/</code>. La tabla común a las gráficas es <code>datos_graficados.csv</code>; <code>proveniencia.json</code> registra su huella SHA-256 y las versiones de las bibliotecas. Las comprobaciones y datos intermedios están en <code>la_vieja/punto_1/</code>. La IA apoyó la programación, la revisión aritmética y la redacción preliminar; el grupo debe revisar fuentes, decisiones e interpretación.</p>
<p>El PDF y el HTML representan los mismos datos. El HTML incluye Plotly y las series, por lo que puede abrirse sin servidor ni Internet; consultar los enlaces externos de fuentes sí requiere conexión.</p>
</section><!-- PROCEDENCIA_FIN -->'''
path=DOC/'informe_interactivo.html'; html=path.read_text(encoding='utf-8')
start='<!-- PROCEDENCIA_INICIO -->'; end='<!-- PROCEDENCIA_FIN -->'
if start in html:
    left,rest=html.split(start,1); _,right=rest.split(end,1); html=left+right
html=html.replace('<footer>',section+'<footer>',1)
path.write_text(html,encoding='utf-8')
tex=r'''\section{Procedencia y alcance}
\subsection{Procedencia de los datos}
Se utiliza CAMELS-COL, depósito del 26 de febrero de 2026, DOI
\href{https://doi.org/10.5281/zenodo.18794895}{10.5281/zenodo.18794895}, consultado
el 21 de septiembre de 2026. El archivo de entrada es
\texttt{Hydromet\_data\_26127040.txt}, incluido en
\texttt{04\_CAMELS\_COL\_Hydrometeorological\_data.zip}, para la cuenca del río
La Vieja hasta la estación Cartago (IDEAM 26127040).
\begin{itemize}
\item \textbf{Precipitación:} CHIRPS v2, datos diarios promediados sobre la cuenca
por los autores de CAMELS-COL, en mm/día. Es un producto combinado, no una
medición directa de un único pluviómetro.
\item \textbf{Caudal:} valores diarios reportados como observados en la estación
hidrométrica IDEAM, distribuidos mediante CAMELS-COL, en m$^3$/s. No se
descargaron aforos originales directamente del IDEAM.
\item \textbf{Área y delimitación:} atributos y polígono CAMELS-COL; área
reportada de 2797,19 km$^2$. Nombre y ubicación contrastados con el catálogo IDEAM.
\item \textbf{Temperatura:} el archivo contiene Tmin y Tmax de MSWX; se grafican sus medias mensuales y una Tmedia estimada como $(Tmin+Tmax)/2$, no una media horaria observada.
\end{itemize}

\subsection{Alcance temporal y procesamiento}
Se analiza enero de 1981 a diciembre de 2022 (42 años). Se reconstruyó el
calendario diario y se conservaron solo meses con el 100\,\% de días válidos:
485 de 504 meses. P mensual es la suma de P diaria; Q mensual es la media de Q
diaria. No se rellenaron faltantes, no se prorratearon sumas ni se eliminaron
extremos por su magnitud.

Las estadísticas globales y por año describen valores mensuales válidos. Mínimo
y máximo no son extremos instantáneos ni diarios. La desviación estándar es
muestral. Los años incompletos describen únicamente su muestra disponible.

\subsection{Limitaciones y trabajo pendiente}
Este documento es una exploración descriptiva inicial. La cartografía de relieve utiliza Copernicus GLO-30, documentado en la sección de mapas. Las gráficas no prueban
tendencias, causalidad ni capacidad predictiva. No se ha certificado la
homogeneidad del registro, la ausencia de reconstrucciones previas o el efecto de
extracciones y regulación. No hay banderas por observación en el archivo diario
que permitan resolver esas cuestiones.

\textbf{IMERG aún no está incorporado:} se verificó cobertura en catálogo, pero
no se descargaron ni validaron valores sobre la cuenca. También quedan pendientes
una temperatura media de fuente directa y los registros individuales de estaciones de lluvia.
El conteo de estaciones no demuestra continuidad de sus series ni significa que
se hayan utilizado como datos de entrada.

\subsection{Reproducibilidad y apoyo de IA}
Los scripts numerados se conservan en \texttt{seleccion\_cuenca/scripts/}.
La tabla común a las gráficas es \texttt{datos\_graficados.csv};
\texttt{proveniencia.json} registra su huella SHA-256 y versiones de bibliotecas.
Las comprobaciones e intermedios están en \texttt{la\_vieja/punto\_1/}.
La IA apoyó la programación, la revisión aritmética y la redacción preliminar;
el grupo debe revisar fuentes, decisiones e interpretación.

PDF y HTML representan los mismos datos. El HTML incluye Plotly y las series y
funciona sin servidor ni Internet; consultar fuentes externas sí requiere conexión.
'''
import re
tex=re.sub(r'\\texttt\{([^}]+)\}',lambda m:r'\path{'+m.group(1).replace(r'\_','_')+'}',tex)
(LATEX/'secciones'/'04_procedencia_alcance.tex').write_text(tex,encoding='utf-8')
main=LATEX/'informe.tex'; content=main.read_text(encoding='utf-8')
if r'\input{secciones/04_procedencia_alcance}' not in content:
    content=content.replace(r'\end{document}',r'\clearpage'+'\n'+r'\input{secciones/04_procedencia_alcance}'+'\n'+r'\end{document}')
main.write_text(content,encoding='utf-8')
print('Procedencia y alcance añadidos al final de ambos documentos.')
