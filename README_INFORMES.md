# Informes de Hidrología

<!-- GENERADORES_PORTABLES_INICIO -->
La reconstruccion ejecutable de la edicion actual se documenta en
`HIDROLOGÍA 2.0/seleccion_cuenca/EJECUTAR_INFORMES.md`.
Ejecutar `scripts/ejecutar_informes.py` desde seleccion_cuenca para generar ambos
informes; `generar_informe_interactivo.py` y `generar_informe_pdf.py` permiten
hacerlo por separado. Las fuentes verificadas estan en `fuentes_informes/`.
Este flujo reproduce la edicion publicada de 486 paginas, sin recalcular los
analisis cientificos ni depender de rutas temporales. La opcion `--publicar`
actualiza las copias principales; la ejecucion predeterminada crea resultados
separados en `salida_informes/`. Los pasos numerados siguientes describen
etapas anteriores y no deben ejecutarse todos para actualizar la edicion final.
<!-- GENERADORES_PORTABLES_FIN -->


La versión integrada actual es `Informe_Hidrologia_actualizado_1_5.pdf`.
Conserva la portada, los puntos 1–3 y el apartado 5.1 e incorpora las cuatro
páginas del punto 4 del commit `d367474dba5fbb1cc9f4ed2906076bbcb2558512`.
Tiene 486 páginas e incorpora el apartado 5.2 y sus 24 láminas (288 mapas),
y el apartado 5.3 con retiro de tendencias, persistencia anual AR(1), FDR BY
global, subperiodos, exclusión de años y 48 láminas de diagnóstico.
El 5.3 empieza en la página 170 del archivo. El 5.4 comienza en la página 225,
con interpretación física, contraste mensual con Niño 3.4 de NOAA PSL,
integración con Fourier, bibliografía regional y síntesis de los cinco puntos.
La inferencia estadística del 5.3 es aproximada y condicionada
a los supuestos documentados; no demuestra causalidad.

El informe interactivo actualizado está en `Informe_Hidrologia_interactivo.html`.
Se abre localmente en un navegador. Se verificaron en Edge la portada,
los numerales 5.1–5.4, la ubicación del contenido y las tres gráficas nuevas,
sin errores JavaScript. Los gráficos requieren acceso a sus bibliotecas externas.

Las versiones canónicas también están en
`HIDROLOGÍA 2.0/seleccion_cuenca/la_vieja/documentos/`.
Los archivos fuente y el registro de páginas y huella SHA-256 de la
integración están guardados en `documentos/apartado_4/`.
Los respaldos previos se conservan localmente.

Para reproducir la base hasta 5.2 ejecutar los scripts 46 y 47 en
`HIDROLOGÍA 2.0/seleccion_cuenca/scripts/`, en ese orden. El 47 conserva
la base con portada y Fourier en `documentos/integracion_final/base_antes_5_2.pdf`.
Para generar 5.3 ejecutar 48, 49 y 50, en ese orden. El script 51 exporta
Excel con @oai/artifact-tool y el 52 verifica el visor sin navegador.
Los scripts 53 y 55 reparan la portada y los numerales del HTML.
Para generar 5.4 ejecutar 56, 57 y 58, en ese orden; 59 verifica el HTML
en navegador y 60 exporta el Excel con @oai/artifact-tool.
Las fuentes, resultados, referencias, Excel y verificaciones de 5.4 están
en `documentos/apartado_5_4/`. NOAA PSL usa ERSST v6 en este contraste;
los mapas previos usan ERSST v5. Es un contraste complementario, no una
replicación independiente ni una prueba causal o de pronóstico.
Los scripts 40, 47 y 50 corresponden a integraciones anteriores y no deben
usarse como último paso para generar la versión con 5.4.

`Informe_Hidrologia_integrado_punto4.pdf` es la versión histórica de 63 páginas.
Usar `Informe_Hidrologia_actualizado_1_5.pdf` para consultar todos los avances.

La ruta `documentos/latex/informe_ordenado.pdf` contiene ahora el PDF integrado
completo, sincronizado mediante el script 61. Conserva los puntos 1-3 de la
compilacion reciente y los puntos 4-5 del informe integrado. El archivo TEX
por si solo no reproduce las laminas integradas: el paso 61 es necesario.

La edición más reciente separa y numera 33 ecuaciones de los puntos 2–5.
Para reproducirla: ejecutar 64, compilar `latex/informe_ordenado.tex`, ejecutar
65, compilar `revision_formulas/bloques.tex`, ejecutar 66 y 67; 68 verifica
las ecuaciones en navegador. Este flujo sustituye al 61 como último paso.
Los respaldos y las verificaciones están en `documentos/revision_formulas/`.

La usuaria autorizó expresamente el 8 de octubre de 2026 aplicar también al
punto 1 los cambios de formato y restaurar la fuente original en todo el
documento. Esta autorización corresponde a tipografía y tablas; se conserva
el contenido científico. La portada del PDF se mantiene idéntica y el índice
refleja la nueva paginación.

La última edición unifica la tipografía y las tablas de los puntos 1–5.
El PDF usa Latin Modern Roman, la familia original del punto 1: títulos 16 pt,
subtítulos 13 pt, encabezados interiores 11,5 pt, texto 10,5 pt y tablas
8,5 pt. Las tablas comparten encabezados azules, filas alternadas y alineación
numérica. Las ecuaciones conservan su composición matemática independiente.
El interactivo incorpora la misma familia y jerarquía, adaptadas a pantalla.

Para reproducir este formato ejecutar el script 74, que prepara las fuentes
originales y ejecuta 75, 76 y 77; el 78 verifica el PDF y el interactivo.
Los respaldos, datos de tablas y verificaciones están en
`HIDROLOGÍA 2.0/seleccion_cuenca/la_vieja/documentos/revision_tablas/`.
Se verificaron 64 tablas del PDF y 53 del interactivo, incluidas las del
punto 1. Una copia anterior de
`documentos/informe_actualizado.pdf` estaba abierta y no pudo sobrescribirse;
el archivo nuevo indicado al inicio contiene la edición completa.

Se desarrolló 1.5.a con una climatología común de 285 meses de 1998–2022
para CHIRPS, IMERG de cuenca, Q, R y temperatura media ERA5-Land. Incluye
cinco tablas de doce meses con n, media, mediana, desviación estándar,
cuartiles y percentiles 10–90; ciclos con bandas interanuales y mapas año–mes.
Sus medias coinciden con las del apartado 5.4. Los incisos 1.5.b y 1.5.c
permanecen pendientes de desarrollo. El nuevo apartado empieza en la
página 54 del archivo; consultar el indice actualizado para el punto 2. Fuentes y verificaciones están
en `documentos/apartado_1_5/`; el script 80 integra PDF y HTML y el 81 los
verifica. Este paso debe ejecutarse después de la unificación del formato.

El contraste de cambios documentados en productos se incorpora al punto 1.4: cuatro casos en las paginas fisicas 48-51. El script 84 conserva la base y reproduce la insercion; el visor HTML mantiene un selector de casos.

El registro tecnico de ocho casos del punto 1.4 se presenta en las paginas fisicas 52-53. El script 85 reproduce esta incorporacion.

Sincronizacion 34d523e: se descargaron los PDF completos mediante Git LFS (480 paginas) y se conservaron los seis folios locales del control 1.4. La version combinada tiene 486 paginas, incorpora las interpretaciones individuales recibidas y mantiene los cuatro contrastes y el registro de ocho casos. El script 86 reproduce esta integracion. Las versiones historicas se conservan.
