"""Introduce el propósito y la lectura de los diagramas sin alterar resultados."""
from pathlib import Path
import re, html, shutil
BASE=Path(__file__).resolve().parents[1]
DOCS=BASE/'la_vieja/documentos'
ROOT=DOCS.parents[3]
OUT=DOCS/'revision_redaccion_2_1'
OUT.mkdir(exist_ok=True)
paragraphs=[
'Los diagramas de dispersión nos permiten explorar cómo se relaciona la lluvia con la respuesta del río La Vieja y qué tan próximas son las estimaciones de precipitación de IMERG y CHIRPS a la medición disponible en Zaragoza-AUT. Buscamos reconocer si los meses más lluviosos suelen acompañarse de mayores caudales, cuánto varía esa respuesta y en qué casos las fuentes de lluvia muestran diferencias. Esta lectura sirve como punto de partida para los modelos de los apartados 2.2 y 2.3: antes de ajustar una relación estadística, necesitamos comprender la forma y las limitaciones de los datos.',
'Para hacerlo, comparamos tres parejas: precipitación satelital y lluvia local, lluvia local y caudal, y precipitación satelital y caudal. Cada punto representa un mes con datos válidos en las dos variables. La lluvia que se utiliza como referencia de la comparación se sitúa en el eje horizontal; en el vertical se representa la lluvia local, el caudal medio Q o la escorrentía R, según el panel. La precipitación y la escorrentía se expresan en mm/mes, y el caudal en m³/s. Los colores distinguen los doce meses calendario y ayudan a observar si la época del año acompaña los agrupamientos de puntos.',
'Al recorrer las gráficas, interesa tanto la dirección de la nube como su amplitud. Una tendencia ascendente indica que, en la muestra, una mayor lluvia suele coincidir con un mayor caudal; la dispersión permite reconocer cuánto puede cambiar el caudal entre meses con precipitaciones parecidas. En la comparación entre fuentes de lluvia, la línea 1:1 ofrece otra referencia: muestra dónde quedarían los puntos si ambas registraran la misma cantidad. Por eso examinamos la asociación y las diferencias de magnitud por separado; una nube alineada no implica necesariamente que las dos fuentes concuerden.',
'La comparación se construye con IMERG Final V07B y CHIRPS promediados sobre la cuenca, mientras que Zaragoza-AUT representa una medición puntual. Para IMERG se utiliza el promedio por área sobre el polígono exacto de La Vieja. Emparejamos únicamente meses completos y simultáneos: la relación IMERG–Q reúne 285 meses entre enero de 1998 y diciembre de 2022, y las comparaciones con Zaragoza disponen de 14 meses completos entre enero de 2018 y agosto de 2019. Aunque el archivo local contiene 22 acumulados no vacíos, ocho corresponden a meses parciales y se excluyen sin rellenarlos ni prorratearlos. Esta diferencia de cobertura y de escala espacial orienta la interpretación: el contraste local es exploratorio y no permite validar por sí solo la lluvia de toda la cuenca.'
]
tex=DOCS/'latex/informe_ordenado.tex'
t=tex.read_text(encoding='utf-8')
shutil.copy2(tex,OUT/'informe_ordenado_antes.tex')
start=t.index(r'\subsubsection*{Datos, ejes y control de completitud}',t.index(r'\subsection{Diagramas de dispersión e interpretación}'))
end=t.index(r'\begin{figure}',start)
body='\n\n'.join(p.replace('m³/s','m$^3$/s').replace('–','--') for p in paragraphs)
t=t[:start]+body+'\n'+t[end:]
tex.write_text(t,encoding='utf-8')
for path in [DOCS/'informe_interactivo.html',ROOT/'Informe_Hidrologia_interactivo.html']:
    s=path.read_text(encoding='utf-8')
    pattern=r'<h3>Datos, ejes y control de completitud</h3><p>.*?</p>'
    s,n=re.subn(pattern,''.join('<p>'+html.escape(p)+'</p>' for p in paragraphs),s,count=1,flags=re.S)
    assert n==1,path
    path.write_text(s,encoding='utf-8')
(OUT/'introduccion_2_1.md').write_text('\n\n'.join(paragraphs),encoding='utf-8')
print('Introduccion actualizada en TEX y ambos HTML; cifras y graficas conservadas.')
