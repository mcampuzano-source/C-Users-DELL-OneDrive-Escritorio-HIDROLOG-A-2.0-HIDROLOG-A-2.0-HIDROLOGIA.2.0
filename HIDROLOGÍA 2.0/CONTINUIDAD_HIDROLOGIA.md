# Continuidad del proyecto de Hidrología

Fecha de preparación: **28 de septiembre de 2026**. Documento para continuar en otra cuenta o chat de Codex. Se redactó leyendo la guía local, los scripts, los resultados y los documentos existentes; no supone una nueva descarga ni una validación externa de las observaciones.

## 1. Leer primero: estado real y próximo paso

El usuario Marcos ya eligió **la cuenca del río La Vieja hasta la estación Cartago, IDEAM 26127040**, con área CAMELS de **2797,19 km²**. No volver a abrir la selección de cuenca sin una razón concreta. Se trabaja paso a paso en dos documentos: un **PDF compilado desde LaTeX con figuras Matplotlib** y un **HTML Plotly autocontenido que funciona sin servidor ni Internet**.

La exploración de precipitación CHIRPS, caudal CAMELS y temperaturas MSWX está implementada. Incluye calendario completo, control de faltantes, series mensuales, estadísticos, histogramas, temperaturas, dispersión CHIRPS–Q, mapas y topografía descargada. **La tarea del profesor NO está terminada:** faltan valores IMERG, series de lluvia terrestre auditadas, completar climatología y relaciones, y desarrollar tendencias, Fourier y mapas de correlación global.

**Siguiente paso recomendado:** resolver una muestra real y verificable de precipitación para las comparaciones. Priorizar el acceso a IMERG, obligatorio en la guía, y en paralelo documental buscar registros terrestres por estación. El usuario respondió expresamente **«No tenemos acceso»** a la pregunta sobre Earthdata/archivos IDEAM. No asumir credenciales disponibles ni pedir contraseñas. La descarga NASA probada respondió HTTP 401; eso describe esa vía, no demuestra que todas las vías públicas estén cerradas. Investigar alternativas oficiales y comprobar archivos, versión, unidades y cobertura antes de anunciar éxito. Para IDEAM, comenzar con consultas pequeñas por código y periodo: la consulta masiva del script 20 agotó el tiempo de espera.

Si el acceso sigue sin resolverse, conservar el bloqueo documentado y avanzar en la climatología 1.5 con CHIRPS/Q/R/temperaturas existentes, indicando que no completa la comparación IMERG. No inventar datos ni presentar catálogos o climatologías publicadas como series descargadas.

## 2. Objetivo, contexto y requisitos del profesor

Fuente normativa: [`tarea_1_202602.pdf`](tarea_1_202602.pdf), 24 páginas. Profesor **Carlos David Hoyos**, Universidad Nacional de Colombia, Sede Medellín, curso Hidrología 202602. El resumen siguiente no sustituye releer el apartado que se vaya a implementar.

Objetivo general: clasificar hidroclimáticamente una cuenca con evidencia mensual, explicando distribución, estacionalidad, cambios temporales y relaciones con el clima regional/global. El trabajo debe conectar resultados con procesos físicos y distinguir observación, inferencia e hipótesis.

### Selección y condiciones de entrada (página 1)

- Grupo de tres estudiantes. No constan aquí los nombres de los otros integrantes ni la distribución de contribuciones: no inventarlos.
- Caudal diario observado y precipitación diaria representativa de la cuenca, con **al menos 25 años comunes**.
- Máximo **10 % de faltantes diarios por variable**, sobre días esperados y antes de rellenar; describir su distribución temporal.
- Área entre **100 y 10 000 km²**, ambos límites incluidos; área correspondiente a la salida y representatividad frente a IMERG.
- IMERG para la misma cuenca y un periodo superpuesto; disponibilidad real por verificar, no solo catálogo.
- Temperatura media mensual de la base o temperatura a 2 m ERA5-Land/ERA5 cuando falte. La estimación actual con Tmin/Tmax debe explicarse y evaluar si basta para el propósito; no es temperatura media observada.
- Identificación con nombre, código, coordenadas, área, mapa y procedencia de delimitación.

### Los cinco puntos y su alcance

1. **Exploración y validación mensual, páginas 3–5.** P acumulada, Q media, R para comparar láminas y Tmedia; series alineadas, unidades y vacíos visibles; incorporar IMERG como promedio de cuenca, no sustituirlo automáticamente por el píxel de salida. Documentar producto, versión, modalidad, variable, unidades y pesos espaciales. Una variable en un archivo mensual puede ser tasa: comprobar y convertir por duración. Histogramas y tablas para P de referencia, IMERG, Q y Tmedia, con R cuando corresponda; n, media, mediana, desviación estándar, mínimo, máximo, rango, cuartiles, IQR, P5/P10/P90/P95. Para comparar lluvias, mismos meses y clases. Diagramas de caja, extremos y ceros. Auditoría de faltantes/fechas/unidades/códigos/duplicados, al menos un mes comprobado manualmente, anomalías registradas sin borrar extremos automáticamente. Climatología de 12 meses con n de años, media, mediana, desviación, cuartiles y P10–P90, bandas o cajas, representación que conserve años individuales, amplitud/picos/estacionalidad, estabilidad entre años y subperiodos, anomalías y explicación física regional.
2. **Relaciones y modelos, página 6.** Dispersión IMERG–P de referencia, P de referencia–Q e IMERG–Q; color por mes. Línea 1:1, sesgo PI−PL, MAE/RMSE para las precipitaciones; Pearson/Spearman; rezagos justificados y anomalías para separar el ciclo anual. Modelos sencillos cuando se justifiquen, sin forzar capacidad predictiva. Validación mediante bloques temporales o años, sin partición aleatoria de meses dependientes; selección y climatología dentro del ajuste; comparar con IMERG sin corrección y climatología de Q. Reportar residuos, unidades, supuestos y evaluación fuera de muestra.
3. **Tendencias, páginas 7–9.** Registros completos disponibles y periodo común por separado; series originales, anomalías mensuales y estandarizadas con referencia fija. Secuencia completa y doce subseries por mes calendario, usando fechas reales. OLS y control estacional, incertidumbre HAC o bloques si corresponde; Mann–Kendall estacional y Sen/Theil–Sen con dependencia considerada; evolución no lineal justificada (LOESS/GAM/segmentada). Pendientes por década, incertidumbre, residuos, sensibilidad, comparaciones múltiples y causas alternativas. No confundir tendencia con atribución causal.
4. **Fourier, página 10.** Secuencias mensuales originales centradas y anomalías, sensibilidad al detrend, espectros unilaterales y documentación de ventana/normalización/unidades/resolución. No eliminar huecos y concatenar meses como consecutivos ni rellenar con cero. Seleccionar tramo continuo o justificar tratamiento y sensibilidad. Examinar 12 meses, 6 meses e interanual; estabilidad y ruido adecuado si se afirma significancia. Potencia no permite inferir fase relativa y un pico no demuestra ENSO.
5. **Correlación con clima global, páginas 11–12.** Campos mensuales de SST y dos variables atmosféricas justificadas, no solo índices escalares. Doce mapas por combinación P/Q con cada campo, a través de los años de cada mes; IMERG para contraste. Anomalías por celda y referencia fija, rezagos explícitos, n efectivo, máscaras, escala −1 a 1, dependencia temporal, FDR u otro tratamiento defendible, detrend y subperiodos. Interpretación de regiones coherentes, alternativas y evidencia física, no causalidad automática.

### Requisitos transversales y entrega

- Página 2: ficha física con relieve, orientación, coberturas, suelos/geología y regulación/extracciones cuando existan. Cada interpretación: resultado cuantificado → mecanismo → evidencia propia y bibliográfica → alternativas y contraste. Citas pertinentes en la discusión; no basta bibliografía final. Cierre con esquema conceptual propio y tabla de resultado/mecanismo/evidencia/fuente/limitación.
- Páginas 13–14: IA Nivel A abierto para apoyo específico; el grupo debe entender, verificar e interpretar. Declarar herramientas/versiones conocidas, tareas, verificaciones, correcciones/rechazos y aportes personales. No presentar una resolución completa delegada como trabajo propio. Evaluación oral sin IA (Nivel C). No consta la versión exacta del modelo usada en todo el historial: no inventarla.
- Informe final: **Introducción; Metodología; Resultados y discusión física; Conclusiones; Uso de IA**, más referencias y anexos pertinentes. El documento actual por apartados incrementales todavía debe adaptarse a esa estructura.
- Entrega según guía: **lunes 5 de octubre de 2026**, único ZIP en Google Classroom con PDF, código, dependencias/versiones, datos utilizados (incluido IMERG y campos climáticos), productos y README con integrantes y ejecución. Los enlaces no sustituyen los archivos usados. Incluir subconjuntos pertinentes, no necesariamente bases nacionales completas.
- Presentaciones según guía: **29 y 30 de septiembre de 2026**, 15 minutos por grupo. No se conoce el turno asignado ni cambios posteriores del profesor. 50 % oral y 50 % informe/material reproducible. La interpretación física concentra 50 % de la nota total y el dominio/defensa otro 10 %.

## 3. Preferencias e instrucciones del usuario

- Trabajar y explicar en español, de manera gradual, con código visible y reproducible desde el inicio.
- Conservar dos productos equivalentes: Matplotlib para LaTeX/PDF y Plotly en un HTML autocontenido, sin servidor. No cambiarlo por una aplicación que necesite servicio o teselas remotas.
- Guardar resultados también en Excel; ya pidió conteos de estaciones, ranking, estadísticas y controles.
- Priorizó mayor número de estaciones de lluvia en tierra y después menores faltantes. La elección de La Vieja está confirmada.
- Mantener control de faltantes, descripción de años/periodos, unidades, procedencia y alcance. Añadir procedencia y alcance al final de ambos documentos.
- Quiere precipitación realmente in situ, no confundirla con CHIRPS. Pidió scatterplots, Tmin/Tmax/Tmedia, mapas y descargar topografía si no existía.
- Última ampliación antes de este traspaso: histogramas y todos los estadísticos del apartado 1.3, R al comparar láminas, unidades, periodo, faltantes y convención de percentiles explícitos.
- Dijo no disponer de acceso a Earthdata; no pedir contraseñas ni suponer que se resolvió. Se continuó con CHIRPS–Q y el resto disponible, dejando las comparaciones faltantes señaladas.
- Este documento es el encargo actual. No interpretar el traspaso como autorización para afirmar que los cinco puntos están resueltos o para publicar/enviar el trabajo.

## 4. Decisiones tomadas y razones

| Decisión | Razón y alcance |
|---|---|
| CAMELS-COL abierto, DOI 10.5281/zenodo.18794895, depósito de 26-02-2026 | La versión referida inicialmente en la guía era restringida. Se descargaron siete archivos y el README registra MD5 coincidentes con Zenodo. Se hallaron 346 series en los archivos; no usar sin matiz las 347 estaciones del manuscrito. |
| La Vieja–Cartago 26127040 | Prioridad lexicográfica de red activa de lluvia y luego faltantes; no es la cuenca de menores faltantes. Sustituye la preferencia inicial por Mulatos, conservada solo como antecedente. |
| 1981–2022 para exploración | Periodo fijo de 42 años, sin seleccionar ventanas por resultados. Para IMERG se catalogó 1998–2022; no recortar todo al registro más corto. |
| Área 2797,19 km² para R | Consistencia con atributos CAMELS. Área geodésica preliminar del polígono ≈2780,18 km² (diferencia ≈0,61 %); reconciliación cartográfica pendiente. |
| Mes válido solo con 100 % de días válidos | Evitar sumas de lluvia parciales y criterios cambiantes. Es decisión metodológica actual, no umbral mensual impuesto literalmente por el profesor. |
| Sin relleno, prorrateo ni eliminación automática de extremos | Mantener trazabilidad y límites de la evidencia. Se conservan ceros; temperatura negativa no es por sí misma inválida. |
| CHIRPS como P de referencia | Disponible en CAMELS y representativa de la cuenca según documentación; producto combinado, no estación puntual ni fuente completamente independiente de otros satélites. |
| Tmedia estimada de extremos MSWX | Permite una primera curva con datos disponibles; claramente rotulada como estimación, no media horaria observada ni ERA5. |
| Topografía Copernicus GLO-30 pública | Se pudo descargar sin Earthdata y cubre toda la cuenca; se guarda resolución nativa y una malla menor solo para visualizar. |

La estación llamada Cartago aparece en el catálogo como Risaralda, municipio Pereira; no cambiar departamento/municipio deduciéndolos del nombre. Consultar las coordenadas exactas en el catálogo y archivos cartográficos, no inventarlas.

## 5. Fuentes, estaciones y accesos: confirmado frente a pendiente

### CAMELS e inventario IDEAM

Datos diarios: miembro `Hydromet_data_26127040.txt` del ZIP hidrometeorológico. Campos originales: Fecha, Precipitacion, ETP_, Temperatura_minima, Temperatura_maxima y Caudal. Según documentación: P CHIRPS v2 en mm/día; Q diario observado en m³/s; Tmin/Tmax MSWX en °C. No hay Tmedia original ni banderas diarias que certifiquen historia de rellenos o calidad del caudal. ETP no se ha convertido en un balance validado.

Conteos dentro del polígono CAMELS mediante cruce espacial del catálogo IDEAM:

- **79** pluviométricas/pluviográficas (PM/PG), **57 activas**.
- **56** meteorológicas multivariable, **39 activas**.
- **92 activas** de categorías con capacidad de medir lluvia, contando códigos únicos en PM/PG/CO/CP/AM/SP/SS. No sumar 92+39: hay solapamiento de categorías.
- Son estaciones inventariadas, no 92 series descargadas ni 92 series con 25 años. Capacidad de medir lluvia inferida de categoría, sensores no auditados individualmente. Estado activo corresponde al catálogo consultado, no a comprobación en tiempo real.

El POMCA de La Vieja, capítulo de clima, tabla 3.7, documenta precipitación terrestre en **Salento 26120160, Alcalá 26120150, Cumbarco 26125130 y Aeropuerto El Edén 26125060**, entre otras. Es evidencia de registros históricos, no entrega local de sus series cronológicas. Revisar correspondencia entre códigos históricos y el catálogo actual antes de descargar: pueden aparecer ceros iniciales, estaciones sustitutas o códigos distintos (el inventario consultado también contiene 26125061). No asumir equivalencia por nombre.

Existe un servicio público IDEAM de precipitación `s54a-sgyg` en datos.gov.co. El script 20 consulta códigos del inventario en bloque y agrupa conteos/fechas. **El intento guardado terminó en timeout**, no en una descarga válida para La Vieja. Revisar semántica de cada sensor: valor de intervalo frente a acumulado, reinicios, unidades, huso horario y frecuencia; no sumar a ciegas datos subdiarios. La presencia de una fila o fechas extremas no demuestra continuidad diaria.

### IMERG

- Catálogo consultado: GPM_3IMERGM versión 07, colección CMR `C2723754851-GES_DISC`; 300 meses catalogados 1998–2022. Es disponibilidad de gránulos globales, no valores válidos extraídos para La Vieja.
- Descarga NASA directa probada: HTTP 401 sin autenticación. No hay precipitación IMERG incorporada al análisis.
- Se calcularon elementos preliminares para la malla; confirmar contra coordenadas reales del archivo obtenido. Promedio por intersección de celdas con el polígono y ponderación por área, incluyendo bordes.
- IMERG mide precipitación, no temperatura. Nunca renombrar CHIRPS como IMERG.

### Topografía ya descargada

- Copernicus DEM GLO-30 Public COG, mosaico `Copernicus_DSM_COG_10_N04_00_W076_00_DEM`.
- DSM: puede incluir vegetación/construcciones; no terreno desnudo. EPSG:4326, resolución 1 segundo de arco (aproximadamente 30 m), alturas EGM2008 en metros.
- Adquisición general TanDEM-X 2011–2015 más rellenos de otras fuentes; no una serie topográfica 1981–2022.
- Recorte: 2 936 002 píxeles válidos, mínimo 908,50 m, máximo 4774,247 m, media de píxeles 1798,951 m. Esa media no está ponderada por área geodésica.
- CAMELS reporta mínimo 940,54 m, media 1826,21 m y máximo 4795 m. No sustituir silenciosamente esos atributos; son modelos/máscaras/resoluciones distintos.
- Conservar aviso de atribución completo en `ATRIBUCION.txt` y metadatos. SHA256 del mosaico: `f820c6b03d629d3d4bfd8728412b24b754a621799fad0e1a8afd6e01b0c4f547`.

## 6. Procedimientos y cálculos reproducibles

1. Reconstruir calendario diario 1981-01-01 a 2022-12-31, incluidos bisiestos. Las fechas omitidas quedan como ausentes.
2. Revisar fechas duplicadas/desordenadas, negativos P/Q, no finitos, códigos de faltantes y Tmin>Tmax. No aplicar rechazo por signo a toda temperatura.
3. Por variable y mes: `cobertura = 100 × días válidos / días esperados`. Retener solo 100 %. Los huecos siguen presentes en el índice mensual, no se concatenan meses.
4. `P_m = suma(P_d)` en mm/mes; `Q_m = media(Q_d)` en m³/s, solo meses completos.
5. `R_m = (86,4 / A_km2) × suma(Q_d)` en mm/mes, equivalente a `Q_m × días_mes × 86,4 / A`. El factor proviene de 86400 s/día, 10^6 m²/km² y 1000 mm/m. Si Q ya viniera en lámina diaria, no repetir conversión.
6. Tmedia estimada diaria `(Tmin_d + Tmax_d)/2`; promediar días completos del mes. Tmin/Tmax mensuales son **medias de los extremos diarios**, no extremos absolutos mensuales.
7. Estadísticos mensuales: cada mes válido tiene igual peso. La media de Q de la tabla no es la media diaria ponderada por duración de mes. Desviación estándar muestral, divisor n−1 (`ddof=1`).
8. Percentiles: interpolación lineal tipo 7, `h=(n−1)p` con índices desde cero; interpolar valores ordenados vecinos. Q1/P25, Q2/P50, Q3/P75; IQR=Q3−Q1; rango=max−min. Mantienen unidades; «convención» de cálculo no implica conversión física.
9. Histogramas: Freedman–Diaconis, ancho teórico `2×IQR/n^(1/3)`, `numpy.histogram_bin_edges(..., bins='fd')` ajusta cantidad entera de clases al rango. Mismos bordes/conteos para Matplotlib y Plotly; barras son porcentaje de meses y suman 100 %, no densidad. Para dos lluvias futuras usar misma muestra y bordes compartidos.
10. Dispersión actual: CHIRPS frente a Q simultáneo, meses pareados, colores por mes calendario; Pearson y Spearman descriptivos, sin prueba de significancia temporal ni causalidad. No se ha implementado toda la comparación de anomalías/rezagos.

## 7. Resultados comprobados y límites

### Disponibilidad y controles

- 15 340 días esperados; 15 085 filas originales; **255 días omitidos (1,6623 %)**.
- **504 meses**, **485 completos**, **19 excluidos**: 6 totalmente ausentes y 13 parciales. Los seis histogramas tienen n=485.
- P/Q comparten fechas ausentes en CAMELS ensamblado; no prueba que CHIRPS original carezca de esas fechas.
- 1998–2022: 285 meses completos de 300 para Cartago; faltantes diarios CAMELS 1,7851 %.
- No se encontraron duplicados/desorden de fechas, P/Q negativos o no finitos, ni Tmin>Tmax en la auditoría local. Eso no certifica homogeneidad ni calidad instrumental.
- Ocho secuencias Q constante de ≥7 días; mayor: 16–26 julio 2004, 11 días, 28,6 m³/s. Se conservan, metadatos pendientes.
- Alertas de cajas 1,5 IQR: 3 meses P, 15 Q, 17 R. No eliminados. Cribado de cambios ×5: dos aumentos P (septiembre 1982 y 2001), ninguno Q; no es prueba de rupturas.
- Huecos largos: diciembre 2007–enero 2008, 62 días; agosto–septiembre 1992, 61; 8 noviembre–31 diciembre 2011, 54.

### Resumen descriptivo (1981–2022, 485 meses por variable)

| Variable | Unidad | Media | Mediana | Desv. muestral | Mínimo | Máximo |
|---|---|---:|---:|---:|---:|---:|
| P CHIRPS | mm/mes | 168,20 | 168,47 | 74,54 | 24,89 | 407,57 |
| Q | m³/s | 98,70 | 85,55 | 64,35 | 18,37 | 508,77 |
| R | mm/mes | 92,82 | 81,40 | 60,63 | 17,59 | 471,45 |
| Media mensual Tmin | °C | 15,06 | 15,02 | 0,58 | 13,56 | 16,75 |
| Media mensual Tmax | °C | 22,40 | 22,39 | 0,91 | 20,25 | 24,83 |
| Tmedia estimada | °C | 18,73 | 18,72 | 0,68 | 17,16 | 20,63 |

Todos los cuartiles, rangos, IQR y P5/P10/P90/P95 están en `documentos/estadisticos_completos.csv` y `.xlsx`. No hay meses completos con P o Q cero; sí hay días sin lluvia.

- P máximo octubre 2022 (407,574 mm), mínimo agosto 1982 (24,892 mm). Q máximo noviembre 2010 (508,7667 m³/s), mínimo julio 1992 (18,3677 m³/s).
- Dispersión CHIRPS–Q, sin rezago, n=485: Pearson **0,5753100412**, Spearman **0,6067929109**. Ciclo anual compartido puede contribuir; no prueba pronóstico ni causa.
- Climatología preliminar P: máximos locales abril 240,16 y octubre 255,03 mm; mínimo julio 89,99 mm. Q: máximos mayo 131,62 y noviembre 157,01 m³/s, mínimo agosto 46,85 m³/s. Sugiere régimen bimodal; un mes de desfase de picos climatológicos no es tiempo de viaje ni análisis formal de rezagos.
- 39–42 años válidos según mes calendario. Falta evaluar estabilidad anual/subperiodos y completar todas las bandas/variables de 1.5.
- R>P en 44 meses; suma R/suma P≈0,552 en meses pareados. No es balance cerrado de 42 años ni P−R es automáticamente evapotranspiración.
- Hipótesis física inicial: dos temporadas lluviosas regionales y posible almacenamiento que prolonga Q. POMCA respalda contexto regional de ZCIT, no demuestra mecanismo local ni atribución ENSO. Regulación, extracciones, orografía, sesgos y delimitación requieren estudio.

### Comprobaciones aritméticas y de documentos

- Enero 1981: 31 días; P=50,945 mm; suma Q diario=1829,3; Qmedio=59,0097 m³/s; volumen=158 051 520 m³; R=56,5037 mm.
- Febrero 1992: 29 días; P=111,351 mm; Qmedio=42,8724 m³/s; R=38,4032 mm. Comprobado bisiesto y equivalencia de fórmulas.
- Sensibilidad Q con ≥90 % de días: 494 meses, media≈100,91 m³/s (+2,24 % respecto al criterio estricto). Solo sensibilidad; no se adoptó ni autoriza completar precipitación.
- PDF actual de 13 páginas compilado con Tectonic; histogramas y tablas inspeccionados visualmente. El número cambiará al añadir secciones.
- HTML probado mediante Playwright/Edge offline: sin solicitudes HTTP ni errores JavaScript, 504 posiciones con 19 nulos por serie P/Q, huecos sin unir, zoom sincronizado y restablecimiento. Script 11 también comprueba tres temperaturas con 485 valores y seis histogramas con 485 meses y 100 % de frecuencia por panel. El JSON de evidencia guarda solo parte de esas comprobaciones; el código contiene las demás aserciones.

## 8. Archivos importantes y ubicaciones

Raíz actual: `C:\Users\Marcos\Desktop\HIDROLOGÍA`. Todas las rutas siguientes son relativas a esa raíz, para que el proyecto pueda moverse. Transferir **la carpeta completa**, no solo este documento.

| Ruta | Contenido / uso |
|---|---|
| `tarea_1_202602.pdf` | Guía original; requisitos por páginas arriba. |
| `seleccion_cuenca/README.md` | Selección, decisiones y avances; contiene antecedentes desactualizados (ver sección 10). |
| `seleccion_cuenca/Filtro_8_cuencas_IMERG.xlsx` | Filtro de ocho cuencas; hojas Ranking estaciones, Inventario estaciones, Metodo estaciones. |
| `seleccion_cuenca/Codigo_desde_el_inicio.html` | Vista legible de scripts 01–20; regenerar con script 06 tras cambios. |
| `seleccion_cuenca/datos/` | Siete originales CAMELS, documentación DOCX, catálogo IDEAM y metadatos NASA/Zenodo. Conservar. |
| `seleccion_cuenca/datos/04_CAMELS_COL_Hydrometeorological_data.zip` | Entrada original diaria; script 08 lee miembro de Cartago. |
| `seleccion_cuenca/datos/03_CAMELS_COL_Basin_boundary.zip` | Polígonos originales, CRS documentado EPSG:3395. |
| `seleccion_cuenca/datos/02_CAMELS_COL_Catchment_information.csv` | Identificación/área CAMELS. |
| `seleccion_cuenca/datos/10_CAMELS_COL_Physiograpic_characteristics.csv` | Atributos fisiográficos. |
| `seleccion_cuenca/datos/catalogo_ideam.json` | Inventario de estaciones; no series de precipitación. |
| `seleccion_cuenca/datos/imerg_catalogo_26127040.json` y `imerg_disponibilidad.json` | Catálogo IMERG, no datos de lluvia de cuenca. |
| `seleccion_cuenca/datos/prueba_acceso_imerg.json` | Diagnóstico de acceso. |
| `seleccion_cuenca/resultados/diario_26127040.csv` | Copia legible preliminar del diario. |
| `seleccion_cuenca/resultados/estaciones_dentro_cuencas.csv` | Inventario espacial de las ocho cuencas; filtrar cuenca_codigo=26127040. Leer código como texto para conservar ceros. |
| `seleccion_cuenca/resultados/ocho_cuencas_wgs84.geojson` | Polígonos transformados. |
| `seleccion_cuenca/la_vieja/punto_1/` | Auditoría inicial, CSV, Excel, figuras e interpretación. |
| `seleccion_cuenca/la_vieja/punto_1/diario_calendario_completo.csv` | Calendario diario reconstruido, huecos conservados. |
| `seleccion_cuenca/la_vieja/punto_1/series_mensuales.csv` | Tabla mensual base P/Q/R/Tmin/Tmax. |
| `seleccion_cuenca/la_vieja/punto_1/resumen_control.json` | Resumen de controles. También intervalos_faltantes, meses_excluidos, secuencias_constantes, valores_invalidos, comprobacion_manual y sensibilidad_completitud_Q en CSV. |
| `seleccion_cuenca/la_vieja/punto_1/Interpretacion_inicial.md` | Interpretación y cautelas; algunas frases sobre Tmedia pendientes son históricas. |
| `seleccion_cuenca/la_vieja/punto_1/Informe_exploracion.html` | Informe inicial, distinto del HTML principal que se amplía. |
| `seleccion_cuenca/la_vieja/punto_1/Exploracion_mensual_La_Vieja.xlsx` | Tablas iniciales y auditoría. |
| `seleccion_cuenca/la_vieja/punto_1/POMCA_capitulo_clima.pdf` | Fuente regional descargada. |
| `seleccion_cuenca/la_vieja/documentos/informe_interactivo.html` | **HTML principal actual**; biblioteca/datos Plotly embebidos. |
| `seleccion_cuenca/la_vieja/documentos/latex/informe.tex` | **Fuente LaTeX principal** con secciones modulares. |
| `seleccion_cuenca/la_vieja/documentos/latex/informe.pdf` | **PDF principal actual**. |
| `seleccion_cuenca/la_vieja/documentos/latex/secciones/` | 01 series, 02 faltantes, 03 estadística por año, 05 temperatura/dispersión/mapas, 06 histogramas, 04 procedencia al final. Números de archivo no son orden de presentación. |
| `seleccion_cuenca/la_vieja/documentos/latex/figuras/` | Matplotlib PDF vectorial y PNG: series, controles, temperatura, dispersión, mapas e histogramas. |
| `seleccion_cuenca/la_vieja/documentos/datos_graficados.csv` | Tabla utilizada en los documentos. |
| `seleccion_cuenca/la_vieja/documentos/temperaturas_mensuales.csv` | Tmin/Tmax y Tmedia estimada para gráficos. |
| `seleccion_cuenca/la_vieja/documentos/estadisticas_globales_y_por_ano.csv` y `Estadisticas_por_ano.xlsx` | Descripción global y por año; no confundir distribución de meses de un año con totales anuales. |
| `seleccion_cuenca/la_vieja/documentos/estadisticos_completos.csv` y `Estadisticos_completos.xlsx` | Estadísticos finales de seis variables, última ampliación. |
| `seleccion_cuenca/la_vieja/documentos/histogramas_clases.json` | Bordes y conteos reproducibles. |
| `seleccion_cuenca/la_vieja/documentos/dispersion_CHIRPS_Q.json` | n, periodo y correlaciones. |
| `seleccion_cuenca/la_vieja/documentos/proveniencia.json` | Huella de entrada y versiones; no sustituye metadatos de todas las fuentes nuevas. |
| `seleccion_cuenca/la_vieja/documentos/verificacion_*.png` y `verificacion_interactivo.json` | Evidencias de pruebas offline. |
| `seleccion_cuenca/la_vieja/topografia/` | Mosaico original, `dem_la_vieja_30m.tif`, `cuenca_la_vieja.geojson`, `relieve_visualizacion.npz`, `metadatos_dem.json`, `ATRIBUCION.txt`. |
| `seleccion_cuenca/la_vieja/estaciones_insitu/error_consulta.json` | URL y timeout de consulta pública; no datos válidos de estaciones. |
| `seleccion_cuenca/herramientas/tectonic/tectonic.exe` | Compilador local Tectonic 0.17.0. |

## 9. Código y reproducción

Scripts bajo `seleccion_cuenca/scripts/`, con rutas derivadas de `__file__`:

| Script | Función |
|---|---|
| `descargar_camels.py`, `revisar_series.py`, `graficar_disponibilidad.py`, `crear_excel.py` | Descarga y filtro inicial, auditoría de candidatas, disponibilidad y Excel inicial. |
| `05_filtrar_temperatura_imerg.py` | Ocho candidatas, temperatura y disponibilidad catalogada IMERG. |
| `06_mostrar_codigo.py` | Actualiza HTML del código desde el inicio. |
| `07_contar_estaciones_ideam.py` | Cruce espacial, conteos, ranking y Excel. |
| `08_exploracion_mensual_la_vieja.py` | Auditoría diaria, agregación, controles, estadísticos y figuras iniciales. |
| `09_informe_exploracion.py` | Informe inicial `punto_1/Informe_exploracion.html`. |
| `10_documentos_series_mensuales.py` | Genera HTML principal y figura base; vuelve a ejecutar ampliaciones según archivos existentes. |
| `11_verificar_documento_interactivo.py` | Prueba offline con Edge/Playwright, zoom, huecos, temperatura, histogramas y gráficos. |
| `12_compilar_latex.py` | Compila PDF con Tectonic local. |
| `13_control_faltantes_documentos.py` | Control mensual y tabla de excluidos en ambos documentos. |
| `14_estadisticas_por_ano.py` | Tablas globales/por año. |
| `15_grafica_cobertura_mensual.py` | Tercera gráfica interactiva: porcentaje de días válidos de cada mes contra fecha. |
| `16_procedencia_alcance.py` | Procedencia/alcance al final; metadatos y límites. |
| `17_topografia_la_vieja.py` | Descarga DEM si falta, recorte, malla visual y metadatos. |
| `18_temperatura_dispersion_mapas.py` | Temperaturas, CHIRPS–Q y mapas offline; secciones Matplotlib/Plotly/LaTeX. |
| `19_histogramas_estadisticas.py` | Seis histogramas, estadísticas CSV/Excel y sección descriptiva en ambos documentos. |
| `20_verificar_precipitacion_insitu.py` | Consulta externa independiente; puede tardar/fallar. No es prerrequisito para regenerar informes actuales. |

Secuencia habitual **desde la raíz del proyecto**, sin volver a descargar datos:

```powershell
python -X utf8 seleccion_cuenca/scripts/10_documentos_series_mensuales.py
python -X utf8 seleccion_cuenca/scripts/12_compilar_latex.py
python -X utf8 seleccion_cuenca/scripts/11_verificar_documento_interactivo.py
python -X utf8 seleccion_cuenca/scripts/06_mostrar_codigo.py
```

Si cambian datos diarios o criterio, ejecutar primero 08; 09 si se desea actualizar también el informe inicial. El 10 encadena 13/14 según secciones existentes, 15/16 según scripts, 18 si hay metadatos topográficos y 19 si existe la sección 06. Al trasladar solo parte de la carpeta podrían omitirse ampliaciones: conservar fuentes y datos. Si se edita únicamente 19, ejecutarlo y después 12/11/06. No editar solo el HTML/PDF generado: modificar el script o fuente que lo construye.

Entorno utilizado: Windows/PowerShell, Python 3.12; versiones registradas en archivos requirements y metadatos. Durante el trabajo se usaron pandas 3.0.6, numpy 2.5.0, matplotlib 3.11.0, openpyxl 3.1.5, plotly 7.1.0, shapely 2.1.2, pyshp 3.1.6, pyproj 3.8.0, rasterio 1.5.1 y playwright 1.63.0. Verificar disponibilidad/compatibilidad en el nuevo entorno: los requirements actuales no reúnen necesariamente todas las dependencias geoespaciales/de pruebas. PyMuPDF (`fitz`) está instalado y se usó para leer/verificar PDF; no hace falta para abrir los informes.

Tectonic puede descargar paquetes la primera vez; el resultado PDF/HTML funciona offline aunque la instalación inicial requiera red. Playwright usa canal `msedge`; si no hay Edge, adaptar la prueba e instalar un navegador compatible. No es dependencia del lector del HTML. No incorporar credenciales en scripts ni en el ZIP.

## 10. Errores, enfoques descartados y advertencias de continuidad

- **Información histórica en README:** aún hay frases como «no se ha seleccionado definitivamente», «temperatura media pendiente» o preferencia por Mulatos. Ya no describen el estado actual: La Vieja fue elegida y existe Tmedia estimada. La revisión de una Tmedia más representativa sí sigue abierta. La misma cautela aplica a la interpretación inicial y al final de `documentos/README.md`. Corregir coherencia al preparar la entrega, sin borrar la historia de decisiones.
- DOI CAMELS antiguo restringido: se usó depósito abierto documentado, no se fingió descargar la versión restringida.
- Intento IMERG sin autenticación falló HTTP 401. Catálogo de 300 meses no equivale a 300 valores de cuenca, ni el Excel de filtro garantiza cobertura válida.
- Consulta masiva de precipitación IDEAM falló por timeout a 90 s. No volver a ejecutarla indefinidamente; reducir por estación/periodo, comprobar esquema y paginación. Un conteo agrupado tampoco resuelve semántica del sensor ni faltantes diarios.
- POMCA aporta climatologías/antecedentes, no reemplaza una cronología de 25 años. No fabricar una serie repitiendo el ciclo medio.
- No simular datos cuando falle acceso; no confundir inventario con medición ni CHIRPS con estación terrestre. No agregar acumulados de sensores sin saber si son incrementales.
- Criterio 90 % para Q solo se exploró como sensibilidad; el resultado principal mantiene 100 %. No rellenar los 19 meses para mejorar apariencia o facilitar FFT.
- La prioridad inicial Mulatos se sustituyó por La Vieja al incorporar el criterio del usuario de red terrestre. San Miguel/La Miel se relegó por regulación documentada y San Agustín por identificación pendiente. No reabrir estas alternativas como decisión activa.
- Un intento de manipular texto LaTeX mediante interpolación PowerShell alteró una fórmula con `$()`; fue corregido. Usar parches o escritura literal segura para LaTeX/Python. No insertar código arbitrario en cadenas de shell.
- PowerShell/terminal puede mostrar acentos corruptos o Python fallar al imprimir símbolos por cp1252. Leer con `-Encoding utf8` y usar `python -X utf8`; no «corregir» archivos UTF-8 buenos por apariencia del terminal. Al preparar este traspaso ocurrió ese error de impresión leyendo la guía; relectura UTF-8 funcionó.
- Si Excel está abierto puede bloquear escritura. Conservar el original y resolver el bloqueo antes de anunciar actualización. No borrar archivos del usuario.
- Inspeccionar las figuras y no asumir que compilación implica legibilidad. Guardar y revisar errores de descarga/lectura, no ocultarlos.

## 11. Pendientes ordenados y límites del avance

1. **Acceso a precipitación:** IMERG real obligatorio y lluvia terrestre solicitada por el usuario. Hacer muestra pequeña, auditar metadatos y semántica, luego ampliar. Conservar original, URL/producto/versión/fecha/unidad/periodo/huella. Reconciliar códigos de estaciones y su ubicación.
2. **Homogeneidad espacial/temporal:** verificar delimitación y salida, diferencia de áreas, celdas IMERG y pesos, continuidad y distribución de estaciones. Definir meses comunes por comparación; no sustituir automáticamente lluvia de cuenca por una estación.
3. **Temperatura:** evaluar y justificar la aproximación Tmin/Tmax; considerar temperatura media original MSWX si disponible o ERA5-Land/ERA5. Mantener fuentes separadas al comparar y documentar cambios.
4. **Completar punto 1:** IMERG en cronología/estadísticos/histogramas/cajas; climatología 1.5 exhaustiva en ambos documentos, bandas y años individuales, estabilidad/subperiodos, anomalías y discusión. Cajas y ciclo preliminar ya existen en `punto_1`, pero no equivalen a todas las comparaciones pedidas ni están todos integrados en el informe principal.
5. **Completar punto 2:** tres pares, línea 1:1 y errores entre lluvias, comparación P–R cuando sea pertinente, anomalías/rezagos y modelos con validación temporal. Hoy solo CHIRPS–Q simultáneo y coeficientes descriptivos.
6. **Puntos 3–5:** pendientes de desarrollar; no hay resultados validados de tendencias, espectros ni campos globales. Elegir métodos y fuentes con el grupo, no escribir conclusiones anticipadas.
7. **Contexto físico:** coberturas, geología/suelos, regulación/extracciones y cambios de estación; leer fuentes regionales, contrastar hipótesis y resolver alertas de Q constante. DEM descargado no resuelve esos temas.
8. **Entrega:** unificar estructura de informe exigida, referencias completas, esquema conceptual y tabla de evidencia, declaración IA y aportes de tres integrantes; actualizar README/dependencias; probar ZIP en carpeta limpia sin recursos externos omitidos. Confirmar con usuario turno de presentación y cualquier cambio del profesor si se necesita planificar, sin asumir datos no conocidos.

## 12. Fuentes para retomar (ya utilizadas, no revalidadas en esta fecha)

- CAMELS-COL: https://doi.org/10.5281/zenodo.18794895 ; metadatos guardados en `datos/zenodo_18794895.json` y documentación DOCX.
- Manuscrito CAMELS-COL identificado durante la revisión como preprint: https://essd.copernicus.org/preprints/essd-2025-200/ . Verificar estado actual antes de llamarlo publicación arbitrada.
- Catálogo IDEAM: https://www.datos.gov.co/resource/hp9r-jxuu.json .
- Registros públicos de precipitación: https://www.datos.gov.co/resource/s54a-sgyg.json ; acceso institucional https://www.ideam.gov.co/transparencia/datos-abiertos/seccion-de-datos-abiertos/precipitacion .
- POMCA La Vieja, capítulo clima: https://www.cvc.gov.co/sites/default/files/Planes_y_Programas/Planes_de_Ordenacion_y_Manejo_de_Cuencas_Hidrografica/La%20Vieja%20-%20POMCA%20en%20Ajuste/Fase%20Diagnostico/3_CapituloI_Diagnostico_Clima.pdf . Copia local disponible. Tabla 3.7 estaciones; sección 3.3, página impresa 20/PDF 24 sobre contexto regional; tabla 3.8, página impresa 36/PDF 40 sobre ciclo. Corroborar las citas concretas al redactar.
- IMERG documentación: https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation . Catálogo https://cmr.earthdata.nasa.gov/search/collections.json?short_name=GPM_3IMERGM&version=07 .
- Copernicus DEM público: https://copernicus-dem-30m.s3.amazonaws.com/readme.html ; DOI https://doi.org/10.5270/ESA-c5d3d65 . URL exacta de mosaico y licencia en metadatos locales.

## 13. Instrucción breve para el nuevo chat

> Lee CONTINUIDAD_HIDROLOGIA.md y la sección pertinente de tarea_1_202602.pdf. Continúa con La Vieja–Cartago 26127040; conserva PDF LaTeX/Matplotlib y HTML Plotly offline y modifica sus generadores. No vuelvas a seleccionar la cuenca. Distingue datos existentes de catálogos y pendientes. Primero revisa el acceso real a IMERG y una muestra de lluvia in situ; si el acceso no se resuelve, documenta el límite y avanza la climatología con los datos disponibles. Explica cada cálculo y permite al grupo revisar decisiones e interpretación. No inventes observaciones, verificaciones ni contribuciones personales.
