# Documentos que se construirán paso a paso

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
