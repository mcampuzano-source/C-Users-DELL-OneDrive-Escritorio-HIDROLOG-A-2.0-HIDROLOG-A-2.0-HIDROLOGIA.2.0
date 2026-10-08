# Informes de Hidrología

La versión integrada actual es `Informe_Hidrologia_actualizado_5_4.pdf`.
Conserva la portada, los puntos 1–3 y el apartado 5.1 e incorpora las cuatro
páginas del punto 4 del commit `d367474dba5fbb1cc9f4ed2906076bbcb2558512`.
Tiene 150 páginas e incorpora el apartado 5.2 y sus 24 láminas (288 mapas),
y el apartado 5.3 con retiro de tendencias, persistencia anual AR(1), FDR BY
global, subperiodos, exclusión de años y 48 láminas de diagnóstico.
El 5.3 empieza en la página 89 del archivo. El 5.4 comienza en la página 140,
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
Usar `Informe_Hidrologia_actualizado_5_4.pdf` para consultar todos los avances.
