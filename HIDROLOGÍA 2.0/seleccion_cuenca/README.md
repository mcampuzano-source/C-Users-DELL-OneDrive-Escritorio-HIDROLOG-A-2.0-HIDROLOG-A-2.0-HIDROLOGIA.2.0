# Selección de cuenca — Tarea 1

## Ampliación: distribuciones, temperatura y topografía

Ambos documentos incluyen histogramas de P CHIRPS (mm/mes), Q (m³/s), R (mm/mes), Tmin, Tmax y Tmedia estimada (°C), con tablas de número de meses válidos, media, mediana, desviación estándar muestral, extremos, rango, cuartiles, IQR y percentiles 5, 10, 90 y 95. Periodo: 1981–2022; 485 meses completos de 504, sin relleno. Percentiles por interpolación lineal tipo 7; R = 86,4 / 2797,19 × suma de Q diario. Tablas exportadas a `la_vieja/documentos/Estadisticos_completos.xlsx` y CSV.

Se añadieron temperaturas mensuales MSWX (Tmedia estimada como promedio diario de Tmin y Tmax), dispersión CHIRPS–Q y mapas de estaciones y relieve. El recorte Copernicus GLO-30 está en `la_vieja/topografia/dem_la_vieja_30m.tif`: modelo de superficie, alturas EGM2008, no serie temporal de elevaciones.

El POMCA documenta precipitación in situ en Salento, Alcalá, Cumbarco y El Edén. Sus series cronológicas aún no están incorporadas. La consulta pública automatizada de IDEAM agotó su tiempo de respuesta; el diagnóstico se conserva en `la_vieja/estaciones_insitu/error_consulta.json`. IMERG y las comparaciones con lluvia terrestre siguen pendientes de datos verificados.

Para regenerar los documentos con los apartados actuales: ejecutar `python seleccion_cuenca/scripts/10_documentos_series_mensuales.py`, después `python seleccion_cuenca/scripts/12_compilar_latex.py` y `python seleccion_cuenca/scripts/11_verificar_documento_interactivo.py`. Los scripts 17–20 contienen la descarga topográfica, mapas, histogramas y consulta de estaciones. `06_mostrar_codigo.py` actualiza la vista del código desde el inicio.

## Documentos LaTeX y Plotly en construcción

Los documentos que se ampliarán paso a paso están en `la_vieja/documentos/`: `latex/informe.tex` contiene el informe LaTeX y `informe_interactivo.html` contiene la versión Plotly autocontenida, sin servidor. Ambos parten de la misma tabla mensual auditada. Las figuras Matplotlib se guardan como PDF vectorial y PNG. El primer apartado muestra P y Q en paneles con eje temporal compartido y meses excluidos visibles. Instrucciones de reproducción en `la_vieja/documentos/README.md`; código en `scripts/10_documentos_series_mensuales.py`.

## Avance: exploración mensual de La Vieja

Ya se generó la primera exploración de P y Q en `la_vieja/punto_1/`. Abrir `Informe_exploracion.html` para ver las figuras, `Interpretacion_inicial.md` para leer la interpretación y `Exploracion_mensual_La_Vieja.xlsx` para revisar los cálculos. Código: `scripts/08_exploracion_mensual_la_vieja.py` y `scripts/09_informe_exploracion.py`.

Resultado: 485 meses completos de 504, con 255 días ausentes (1,6623 % de 1981–2022). No se rellenaron datos ni se eliminaron extremos. Se documentan ocho secuencias de caudal constante que requieren metadatos. IMERG y temperatura media siguen pendientes, por lo que esta exploración no cierra todo el punto 1.

## Cuenca elegida por el grupo

**Decisión confirmada el 21 de septiembre de 2026: trabajar con la cuenca del río La Vieja hasta la estación Cartago, código IDEAM 26127040.** Las otras siete cuencas quedan como antecedentes de la comparación, no como opciones pendientes de elección.

- Área reportada por CAMELS: **2797,19 km²**.
- Registro principal: **1981–2022**, con vacíos conservados.
- Periodo común inicial para comparar con IMERG: **1998–2022**; cobertura catalogada, pendiente de descarga y validación de valores.
- Precipitación de referencia: CHIRPS v2 incluida en CAMELS; caudal observado reportado por CAMELS; temperaturas mínima y máxima: MSWX.
- Faltantes CAMELS en 1998–2022: **1,7851 %**. Los registros de lluvia de las estaciones IDEAM individuales todavía no se han auditado.

La elección está tomada. Antes del análisis definitivo quedan por verificar la delimitación y su estación de salida, las intervenciones que afectan el caudal, el acceso a IMERG y la fuente de temperatura media. Los apartados siguientes documentan el proceso de preselección y sus preferencias anteriores.

## Actualización: candidata principal por red de estaciones en tierra

Con el criterio solicitado de priorizar más estaciones de precipitación y luego menores faltantes, **La Vieja — estación Cartago (26127040)** pasa a ser la candidata principal. Esta actualización reemplaza la preferencia inicial por Mulatos que se conserva abajo como antecedente de la revisión.

El cruce espacial del catálogo IDEAM con los polígonos CAMELS identifica en La Vieja **56 estaciones meteorológicas multivariable (39 activas)** y **79 pluviométricas/pluviográficas (57 activas)**. Al reunir PM, PG, climatológicas, agrometeorológicas y sinópticas, sin duplicar códigos, resultan **92 estaciones activas de categorías que miden lluvia**. Estas categorías se solapan con las multivariable: no sumar 92 + 39. La capacidad de medir lluvia se infiere de la categoría; no se verificaron sensores o series individuales.

Para 1998–2022, los faltantes de las series CAMELS P/Q/Tmin/Tmax en La Vieja son **1,7851 %**. No es el mínimo de las ocho: La Bodega presenta **0,7885 %**, con 12 estaciones activas de lluvia. La prioridad es lexicográfica (más estaciones activas de lluvia, luego menos faltantes CAMELS); el Excel también identifica las opciones no dominadas entre ambos criterios.

Se añadieron al Excel `Filtro_8_cuencas_IMERG.xlsx` las hojas **Ranking estaciones**, **Inventario estaciones** y **Metodo estaciones**. El inventario contiene código, categoría, estado, coordenadas y fecha de instalación de cada estación dentro o sobre el borde de los polígonos. Código reproducible: `scripts/07_contar_estaciones_ideam.py`. La revisión usa el catálogo descargado de https://www.datos.gov.co/resource/hp9r-jxuu.json, no pretende cubrir todas las redes de otras entidades. Los faltantes de las estaciones meteorológicas individuales **no están evaluados**, y estado activo no implica 25 años completos de operación.

## Resultado de la revisión

Se descargó y revisó CAMELS-COL, versión depositada el 26 de febrero de 2026, DOI https://doi.org/10.5281/zenodo.18794895. Los archivos contienen 346 series. El DOI de la guía remite a una versión anterior, actualmente restringida; la actualización es abierta. Se verificaron los MD5 de los siete archivos descargados frente al registro de Zenodo: todos coinciden.

**102 cuencas pasan el filtro cuantitativo de área (100–10 000 km²) y máximo 10 % de faltantes de precipitación y caudal en el periodo fijo 1981–2022 (42 años).** Esto no certifica ausencia de errores, rellenos previos o intervención humana. No se ha seleccionado definitivamente una cuenca.

| Candidata | Código IDEAM | Área CAMELS (km²) | Faltantes P y Q, 1981–2022 | Meses completos P–Q / 504 |
|---|---:|---:|---:|---:|
| Río Mulatos, Pueblo Nuevo, Antioquia | 12027050 | 1031,21 | 1,1343 % | 461 |
| Río Atá, Gaitania, Tolima | 22027020 | 919,26 | 1,6819 % | 481 |
| Río La Vieja, estación Cartago | 26127040 | 2797,19 | 1,6623 % | 485 |

Tanto CAMELS como el catálogo IDEAM ubican la estación denominada Cartago en Risaralda; el catálogo indica municipio Pereira. Se conserva esa identificación, sin inferir el municipio a partir del nombre de la estación.

**Primera candidata propuesta: Mulatos en Pueblo Nuevo**, por su registro extenso, bajo porcentaje de faltantes, tamaño intermedio y menor rango altitudinal reportado (54–1147 m) frente a las dos alternativas. Esta preferencia es práctica, no una demostración de mejor calidad. Su relación preliminar de láminas R/P es aproximadamente 0,21 en meses completos pareados: requiere evaluar balance, delimitación y sesgo de precipitación antes de interpretar pérdidas. Gaitania ofrece más meses completos y sería una alternativa útil para estudiar una cuenca de montaña (1211–4435 m).

San Miguel (23057140, río La Miel) tiene excelente disponibilidad, pero se deja en segundo plano porque existe regulación hidroeléctrica documentada. San Agustín (21017020) también tiene buena disponibilidad, pero se encontraron denominaciones de corriente distintas en fuentes oficiales; no se prioriza sin resolver su identificación y delimitación.

## Qué se comprobó en los archivos

- Se reconstruyeron calendarios diarios completos, incluidos años bisiestos. Los porcentajes usan todos los días esperados, no solo las filas presentes.
- Se evaluaron dos periodos fijos: 1981–2022 y 1998–2022. No se buscaron ventanas para maximizar correlaciones o tendencias.
- Se comprobaron fechas y duplicados; los negativos en P/Q se contabilizan y se consideran inválidos para el filtro. Los ceros se conservan.
- En las cinco candidatas examinadas en detalle no aparecieron valores negativos en P/Q ni fechas duplicadas.
- Hay fechas ausentes en el archivo completo, por lo que P y Q tienen el mismo porcentaje de faltantes en las candidatas. Esto no demuestra que CHIRPS carezca de esos días: pueden haberse omitido al ensamblar CAMELS.
- Para esta preselección se cuenta como completo solo un mes con el 100 % de días válidos. No se rellenó ni prorrateó ningún dato.
- El archivo diario contiene Fecha, Precipitacion, ETP_, Temperatura_minima, Temperatura_maxima y Caudal. No incluye temperatura media ni banderas de calidad por observación. La descripción general del repositorio no basta para verificar la historia de control de calidad o rellenos del caudal.
- Según la documentación descargada, P procede de CHIRPS v2 (mm/día), Tmin/Tmax de MSWX (°C) y Q corresponde a caudal diario observado (m³/s). CHIRPS es un producto combinado; no equivale a observación puntual independiente de productos satelitales.
- No se calculó temperatura media como si estuviese observada. Se deberá justificar una estimación con Tmin/Tmax o usar temperatura media de ERA5-Land/ERA5.

## IMERG y delimitación

Se consultó directamente el catálogo CMR de NASA para GPM_3IMERGM versión 07, colección C2723754851-GES_DISC. El catálogo actual declara cobertura global y comienzo en enero de 1998. Se guardaron los metadatos y el inventario de gránulos 1998–2022; las fechas históricas de inicio pueden diferir de documentación antigua. Es una comprobación de disponibilidad de archivos, **no una descarga ni validación de precipitación IMERG para los polígonos**.

En 1998–2022, Pueblo Nuevo dispone de 268 meses completos de P/Q de 300, Gaitania de 277 y Cartago de 285. Los faltantes diarios respectivos son 0,9966 %, 2,8255 % y 1,7851 %.

La malla nominal de 0,1° de IMERG equivale aproximadamente a 122 km² por celda en Pueblo Nuevo: su área equivale a unas 8,4 celdas completas. Es una aproximación de escala, no un conteo de celdas intersectadas. Se descargaron los polígonos CAMELS, cuyo CRS documentado es EPSG:3395. El promedio IMERG requerirá intersecciones y pesos por área real, incluidos bordes; no usar solo el píxel de la estación.

Antes de cerrar la selección: comprobar geometría y salida del polígono, contrastar área con IDEAM, revisar embalses/extracciones y antecedentes del caudal, y extraer una muestra de IMERG para el polígono. La presencia en catálogo no confirma la validez de todos los píxeles de una cuenca.

## Fuentes consultadas

- CAMELS-COL, datos y documentación: https://doi.org/10.5281/zenodo.18794895
- Manuscrito CAMELS-COL, aún identificado como preprint en revisión: https://essd.copernicus.org/preprints/essd-2025-200/
- Catálogo IDEAM: https://www.datos.gov.co/resource/hp9r-jxuu.json
- IDEAM, ENA 2022, anexo 5c (identifica Pueblo Nuevo–Mulatos y Gaitania–Atá): https://www.ideam.gov.co/file-download/download/public/2842
- CORNARE, regulación de La Miel: https://observatorioambiental.cornare.gov.co/wp-content/uploads/2025/10/INFORME_RONDAS_HIDRICAS_SANMIGUEL.pdf
- IMERG, documentación oficial: https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation
- Catálogo NASA: https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM&version=07
- Alternativas consultadas a nivel documental, sin auditar sus series: CAMELS-CL https://hess.copernicus.org/articles/22/5817/2018/ y CAMELS-BR https://essd.copernicus.org/articles/12/2075/2020/. Ambas incluyen series y atributos; no se descargaron al encontrar opciones colombianas que pasan el filtro.

## Archivos y reproducción

- `datos/`: originales CAMELS, respuesta del catálogo IDEAM y metadatos NASA/Zenodo.
- `resultados/revision_todas_cuencas.csv`: 346 cuencas y dos periodos, incluidas las rechazadas por el filtro.
- `resultados/candidatas_42_anos.csv`: las 102 que pasan el filtro fijo de 42 años.
- `resultados/disponibilidad_mensual_candidatas.csv`: días válidos por variable y mes para cinco candidatas.
- `resultados/diario_*.csv`: copia legible de las series candidatas, sin relleno.
- `resultados/mensual_preliminar_*.csv`: P y Q mensuales exclusivamente de meses completos; no son el análisis definitivo del punto 1.

Desde la carpeta Hidrología ejecutar `python seleccion_cuenca/scripts/descargar_camels.py`, luego `python seleccion_cuenca/scripts/revisar_series.py` y `python seleccion_cuenca/scripts/graficar_disponibilidad.py`. Los dos catálogos externos se conservan como entradas descargadas de las URL indicadas. Dependencias de análisis: Python 3.12, pandas 3.0.6, numpy 2.5.0 y matplotlib (versión registrada en requirements_revision.txt).

Apoyo de IA: búsqueda de fuentes, descarga, programación y cálculo del filtro preliminar. El grupo debe comprobar las fuentes, revisar las candidatas y justificar su decisión e interpretación.
