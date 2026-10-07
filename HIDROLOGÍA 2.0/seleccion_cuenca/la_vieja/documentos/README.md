# Documentos que se construirán paso a paso

## Orden de la guía (4 de octubre de 2026)

Actualización posterior: el 1.2 incorpora IMERG Final V07B ponderado sobre el polígono exacto (300 meses válidos; 42 celdas, 31 de borde). El 1.3 incorpora ERA5-Land y ese IMERG en tablas, histogramas y cajas de los mismos 285 meses completos. Los antecedentes de caja y MSWX permanecen separados. Datos, Excel, pesos, huellas, requisitos y reproducción: [imerg_poligono/README.md](imerg_poligono/README.md). Reproducir primero con el script 22 y después con el 21.

`informe_interactivo.html` y `informe_actualizado.pdf` están organizados por los puntos 1–5, con los apartados 1.1–1.5 y el contexto geográfico al inicio. Los apartados sin desarrollo se identifican como pendientes. La reorganización conserva datos, resultados, figuras y textos de las versiones anteriores, incluidas sus inconsistencias de actualización.

La fuente del PDF ordenado es `latex/informe_ordenado.tex`. Para reproducir la organización después de regenerar los documentos, ejecutar `python seleccion_cuenca/scripts/21_ordenar_informes.py` desde la carpeta Hidrología. Este script utiliza las secciones originales, compila el PDF ordenado y actualiza `informe_actualizado.pdf`; no recalcula series ni figuras. El script de compilación anterior y `latex/informe.tex` conservan la estructura histórica.

Se verificó que los datos de las ocho gráficas Plotly originales permanecen idénticos y que el inventario de figuras LaTeX se conserva, incluidas las repeticiones existentes. Después de la reorganización se corrigieron dos errores de visualización preexistentes: la inserción de la lectura IMERG usa la propia gráfica si no encuentra una sección contenedora, y los títulos de ejes IMERG se actualizan como objetos completos. La lectura temporal y la gráfica IMERG–R–temperatura vuelven a aparecer. Se comprobó la apertura sin errores JavaScript y la igualdad de los datos de las ocho gráficas anteriores; no se recalcularon series ni resultados.

## Ampliación: temperatura, dispersión y mapas

Se añadieron Tmin/Tmax mensuales de MSWX y **Tmedia estimada** mediante el promedio diario `(Tmin+Tmax)/2` seguido de la media mensual. No es una media horaria observada. Se usa el criterio de meses completos.

Se presenta dispersión CHIRPS–Q; IMERG–estaciones y IMERG–Q no pueden calcularse aún: el acceso NASA devuelve HTTP 401 y el grupo no dispone de acceso. Tampoco hay series terrestres descargadas. No confundir CHIRPS con medición en tierra.

Se descargó Copernicus GLO-30 (mosaico N04/W076, unos 30 m) y se guardó el recorte en `../topografia/dem_la_vieja_30m.tif`. Los mapas muestran delimitación, estación Cartago, red terrestre inventariada y relieve. Sus datos están incluidos en el HTML sin teselas de Internet. El producto es un DSM, con vegetación y construcciones; la cartografía y los resúmenes no sustituyen automáticamente los atributos CAMELS. Fuente, licencia y huella de descarga en `../topografia/metadatos_dem.json`.

Reproducir: `scripts/17_topografia_la_vieja.py`, `scripts/18_temperatura_dispersion_mapas.py`, `scripts/12_compilar_latex.py`. El script 10 conserva estas ampliaciones cuando los datos topográficos ya están disponibles. Dependencias adicionales: rasterio, pyproj y shapely.

## Paso 2: control de faltantes

Ambos documentos incluyen distribución año–mes de disponibilidad y tabla de los 19 meses excluidos (seis totalmente ausentes, trece parciales), 255 días faltantes por variable, criterio del 100 % de días válidos y consecuencias para la interpretación. El HTML incluye consulta por celda y filtro de tabla por año/mes. No confundir estos faltantes CAMELS con datos de IMERG o de las estaciones pluviométricas individuales.

Código: `scripts/13_control_faltantes_documentos.py`. Ejecutarlo y luego `scripts/12_compilar_latex.py` para actualizar ambos documentos. El script 10 también conserva automáticamente este apartado al regenerar el HTML. La fuente LaTeX adicional está en `latex/secciones/02_control_faltantes.tex`.

- `latex/informe.tex`: documento principal editable. Añadir cada próximo apartado en `latex/secciones/` e incorporarlo con `\input`.
- `latex/informe.pdf`: PDF compilado realmente desde LaTeX.
- `latex/figuras/series_mensuales.pdf`: figura vectorial Matplotlib para insertar en LaTeX; también se guarda PNG a 300 dpi.
- `informe_interactivo.html`: Plotly autocontenido, con biblioteca y datos incluidos. Abrir por doble clic, sin servidor ni Internet. Zoom sincronizado, selector de fechas, consulta de valores y meses excluidos, exportación SVG.
- `datos_graficados.csv` y `proveniencia.json`: mismos datos para ambas representaciones y huella del archivo de entrada.

## Reproducción

1. Si se modifican los datos diarios o el criterio de completitud, regenerar primero con `python seleccion_cuenca/scripts/08_exploracion_mensual_la_vieja.py`.
2. Ejecutar `python seleccion_cuenca/scripts/10_documentos_series_mensuales.py` para generar las figuras y el HTML.
3. Compilar desde `seleccion_cuenca/la_vieja/documentos/latex` con `tectonic informe.tex` (o `pdflatex informe.tex` dos veces).

Con el compilador local ya instalado, el paso 3 también se ejecuta desde Hidrología con `python seleccion_cuenca/scripts/12_compilar_latex.py`.

Se verificó el HTML con Edge en modo sin conexión: sin peticiones HTTP, sin errores JavaScript, 504 posiciones mensuales y 19 vacíos por serie, zoom sincronizado y botón de restablecimiento. Evidencia en `verificacion_interactivo.json`. La comprobación opcional usa Playwright y `scripts/11_verificar_documento_interactivo.py`; Playwright no es necesario para abrir ni compartir el HTML.

Se descargó Tectonic 0.17.0 desde su publicación oficial de GitHub a `seleccion_cuenca/herramientas/tectonic/tectonic.exe`. La primera compilación puede descargar paquetes tipográficos. El PDF y el HTML resultantes funcionan sin conexión; esta condición no implica que la primera instalación del compilador sea sin conexión.

Paso actual: series mensuales de P CHIRPS y Q observado reportado por CAMELS, 1981–2022. 485 meses completos, 19 excluidos. IMERG y temperatura media no están incorporados. No hay datos sintéticos ni interpolaciones. Los nombres y criterios se mantienen iguales en ambos documentos.


## Actualizacion del 6 de octubre: puntos 2.1 y 2.2

Se incorporan diagramas CHIRPS debajo de IMERG, comparacion de fuentes con muestras comunes y modelos para lluvia local y caudal. Zaragoza tiene 14 meses completos, no 22. Los modelos de caudal se eligen con bloques temporales de desarrollo; 68 meses de 2017-2022 quedan reservados, sin evaluar, para el 2.3. Detalles, rangos, ecuaciones y reproduccion: [apartado_2_2/README.md](apartado_2_2/README.md). Ejecutar el script 35 al final para regenerar ambos informes y conservar los puntos 2.1 y 2.2.
