# IMERG sobre el polígono de La Vieja — 4 de octubre de 2026

Actualización de los apartados 1.2 y 1.3. Los resultados anteriores de Giovanni (promedio de caja) y MSWX permanecen en el informe como antecedentes, con sus fuentes y muestras propias. No se modifica ningún archivo fuente, caudal, CHIRPS ni temperatura anterior.

## Datos y ponderación

- 300 HDF5 originales IMERG Final V07B, enero de 1998–diciembre de 2022: enero está en la raíz del proyecto y los otros 299 en `GPM_3IMERGM_07`.
- Variable `Grid/precipitation`: tasa media mensual en mm/h. Acumulado mensual = tasa × 24 × días reales del mes; se incluyen bisiestos.
- Polígono CAMELS La Vieja–Cartago. 42 celdas intersectadas, 31 de borde; cobertura espacial 100 %. Área geodésica aproximada 2780,18 km². El área CAMELS de 2797,19 km² utilizada para R no cambia.
- Las celdas conservan su lluvia original. Se reconstruyen límites contiguos de la malla nominal de 0,1° porque los límites float32 originales presentan pequeños solapes. Ambos límites se guardan. Se calculan intersecciones y áreas WGS84 con segmentos de máximo 0,001°; la suma de áreas coincide con la del polígono dentro de una tolerancia relativa de 0,000001.
- Pesos = área de intersección / suma de áreas intersectadas. Si alguna celda es inválida, se excluye el mes sin rellenar ni renormalizar. Todos los 300 meses tienen datos válidos.

## Productos

- `IMERG_mensual_poligono_1998_2022.csv`: lluvia de cuenca, tasa, duración y cobertura mensual.
- `pesos_celdas.csv`: coordenadas, límites originales/reconstruidos, áreas y pesos.
- `manifest_archivos.csv`: 300 archivos fuente, tamaños y SHA256.
- `precipitacion_celdas_mm_h.npz`: 300 × 42 tasas originales, pesos, coordenadas y meses.
- `series_alineadas.csv`: calendario 1981–2022; IMERG disponible solo desde 1998; vacíos conservados.
- `meses_comunes_285.csv`: muestra idéntica para CHIRPS, IMERG de polígono, Q, R y ERA5-Land.
- `estadisticos_registros.csv` / `estadisticos_periodo_comun.csv`: coberturas completas por fuente y 285 meses comunes, por separado; incluyen extremos fechados y todos los percentiles pedidos.
- `clases_histogramas.json`: bordes y conteos; las dos precipitaciones comparten exactamente meses y clases.
- `Punto_1_2_y_1_3.xlsx`: series, muestras, estadísticas y pesos.
- `metadatos.json` y `requirements.txt`: procedencia, método y versiones.
- `apartado_1_2.tex` / `apartado_1_3.tex`: contenido integrado en el PDF ordenado. Las figuras nuevas están en `../latex/figuras/imerg_poligono_*.pdf`.

## Reproducción

Desde la carpeta `HIDROLOGÍA 2.0`:

```powershell
python -m pip install -r seleccion_cuenca/la_vieja/documentos/imerg_poligono/requirements.txt
python seleccion_cuenca/scripts/22_imerg_poligono_estadisticas.py
python seleccion_cuenca/scripts/21_ordenar_informes.py
```

El segundo script compila y actualiza `informe_actualizado.pdf` y organiza el HTML. No usar los scripts históricos para sustituir esta actualización sin volver a ejecutar los pasos anteriores.

## Alcance y comprobaciones

El 1.2 tiene producto, versión, modalidad, resolución, unidades, conversión, periodo, ponderación, bordes, cobertura, serie cronológica y acceso reproducible documentados. El 1.3 tiene las tablas, histogramas, cajas e interpretación inicial nuevas; queda profundizar el contraste de episodios extremos y cerrar la discusión física con el grupo. La malla de unos 11 km no resuelve toda la variabilidad del relieve; cobertura completa no demuestra exactitud de la estimación.

Se verificaron la secuencia de 300 meses, versión, coordenadas, unidades y valores de las celdas relevantes; pesos normalizados y cobertura; equivalencia entre suma manual y producto matricial; febrero de 2000 (696 horas) y febrero de 2001 (672); clases compartidas y frecuencias; concordancia de medias Excel/CSV; apertura HTML sin errores JavaScript y conservación de los datos de las gráficas históricas.
