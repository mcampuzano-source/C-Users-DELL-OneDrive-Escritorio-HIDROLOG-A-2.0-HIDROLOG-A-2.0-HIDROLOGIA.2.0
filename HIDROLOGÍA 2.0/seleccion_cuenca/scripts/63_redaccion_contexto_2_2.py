"""Redacción contextual del inicio de 2.2, sin subtítulo introductorio."""
from pathlib import Path
import re, html
DOCS=Path(__file__).resolve().parents[1]/'la_vieja/documentos'
ROOT=DOCS.parents[3]
paragraphs=[
'Después de explorar las relaciones entre lluvia y caudal en los diagramas del apartado 2.1, buscamos establecer si esas asociaciones pueden traducirse en estimaciones útiles. Para ello construimos modelos estadísticos sencillos con dos propósitos: estimar la lluvia mensual de Zaragoza-AUT a partir de IMERG o CHIRPS, y estimar el caudal medio mensual del río La Vieja a partir de la precipitación de cuenca. También examinamos la relación entre lluvia local y caudal como un ejercicio exploratorio. El interés no está únicamente en encontrar una ecuación que se ajuste a los puntos, sino en comprobar si incorporar la lluvia mejora la estimación frente a referencias sencillas, como la media o el comportamiento habitual de cada mes.',
'En estos modelos, P(t) representa la precipitación de cuenca del mes t y L(t) la lluvia local, ambas en mm/mes; Q(t) corresponde al caudal medio mensual, expresado en m³/s. IMERG se obtiene mediante un promedio por área sobre el polígono exacto de La Vieja. Comparamos las dos fuentes de precipitación en las mismas fechas para que las diferencias de desempeño respondan al modelo y al producto utilizado, y no a periodos distintos. Además de la lluvia del mes analizado, consideramos la del mes anterior como una forma sencilla de explorar la posible influencia de condiciones antecedentes sobre el caudal.',
'Esta comparación requiere que estén disponibles, simultáneamente, el caudal y la lluvia de IMERG y CHIRPS tanto en el mes actual como en el anterior. Al aplicar ese criterio, quedan 274 meses completos entre 1998 y 2022, once menos que los 285 pares contemporáneos del apartado 2.1; los faltantes se conservan sin rellenarlos. Organizamos esta muestra en el tiempo: los 206 meses disponibles hasta diciembre de 2016 se destinan al desarrollo y la selección de los modelos, mientras que los 68 meses de 2017–2022 se reservan para la evaluación del apartado 2.3. Así podemos elegir las ecuaciones con información del periodo de desarrollo y comprobar después cómo funcionan en meses que no intervinieron en esa elección.'
]
tex=DOCS/'latex/informe_ordenado.tex'
s=tex.read_text(encoding='utf-8')
start=s.index(r'\subsubsection*{Objetivos, variables y muestras comunes}',s.index(r'\subsection{Modelos estadísticos de lluvia y caudal}'))
end=s.index(r'\subsubsection*{Relaciones candidatas',start)
body='\n\n'.join(p.replace('m³/s','m$^3$/s').replace('–','--') for p in paragraphs)
tex.write_text(s[:start]+body+'\n'+s[end:],encoding='utf-8')
for path in [DOCS/'informe_interactivo.html',ROOT/'Informe_Hidrologia_interactivo.html']:
    s=path.read_text(encoding='utf-8')
    s,n=re.subn(r'<h3>Objetivos, variables y muestras comunes</h3><p>.*?</p>',''.join('<p>'+html.escape(p)+'</p>' for p in paragraphs),s,count=1,flags=re.S)
    assert n==1,path
    path.write_text(s,encoding='utf-8')
print('2.2 actualizado en TEX y HTML sin subtitulo introductorio.')
