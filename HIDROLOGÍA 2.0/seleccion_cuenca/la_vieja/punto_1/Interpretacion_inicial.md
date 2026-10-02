# La Vieja–Cartago: primera interpretación mensual

Estación IDEAM 26127040. Periodo: enero de 1981 a diciembre de 2022. Área utilizada: 2797,19 km², reportada por CAMELS. Esta es la exploración inicial de precipitación y caudal; no es todavía el punto 1 completo, porque faltan IMERG y la temperatura media.

## 1. Fuentes y procedimiento

Se leyó directamente el archivo `Hydromet_data_26127040.txt` del depósito [CAMELS-COL](https://doi.org/10.5281/zenodo.18794895). La precipitación corresponde a CHIRPS v2 promediado sobre la cuenca, no a una estación pluviométrica local. El caudal se reporta como observado en la estación de salida. El archivo no incluye banderas diarias que permitan certificar la ausencia de reconstrucciones previas. La existencia de numerosas estaciones terrestres en el catálogo no significa que sus registros se hayan incorporado a esta exploración.

Primero se reconstruyó el calendario de 15.340 días, incluidos los bisiestos. Los días omitidos permanecen como valores ausentes. Se conservó un mes únicamente cuando todos sus días eran válidos para la variable correspondiente: precipitación mensual = suma diaria; caudal mensual = media diaria. No se rellenaron ni prorratearon meses y se conservaron los ceros.

La lámina mensual de escorrentía se obtuvo mediante `R = 86.4 / 2797.19 × suma(Q_diario)`, en mm/mes. Se comprobó también su equivalencia con `Q_medio × días_del_mes × 86.4 / área`. R es una transformación de Q, no una medición independiente.

## 2. Disponibilidad y problemas detectados

- El archivo contiene **15.085 filas y omite 255 días**, equivalentes al **1,6623 %** del calendario completo. En P y Q faltan exactamente las mismas fechas. Esto describe el archivo ensamblado CAMELS; no demuestra que CHIRPS original carezca de esas fechas.
- Quedan **485 meses completos de 504 (96,23 %)**. Los **19 meses excluidos** siguen apareciendo como vacíos en la serie; las franjas grises de la figura 1 los identifican.
- Los vacíos más largos son **diciembre de 2007–enero de 2008 (62 días)**, **agosto–septiembre de 1992 (61 días)** y **8 de noviembre–31 de diciembre de 2011 (54 días)**. El resto está documentado en `intervalos_faltantes.csv` y `disponibilidad_mensual.csv`.
- No se encontraron fechas duplicadas o desordenadas, P/Q negativos o no finitos, ni Tmin mayor que Tmax. Esto es control básico, no certificación de homogeneidad o exactitud.
- Se detectaron **ocho secuencias de caudal exactamente constante de siete o más días**. La más larga es de **11 días, 16–26 de julio de 2004, con 28,6 m³/s**. Se conservan: pueden relacionarse con redondeo, persistencia real o procesamiento previo. Se necesitan metadatos para distinguir esas posibilidades.
- Los diagramas de caja señalan **3 meses extremos de P, 15 de Q y 17 de R**, mediante bigotes de 1,5 IQR. Son alertas exploratorias que mezclan meses de distintas estaciones del año; ninguno se eliminó por ese criterio.
- El cribado de cambios mensuales por un factor de al menos cinco detectó dos aumentos de P: septiembre de 1982 y septiembre de 2001. Coinciden con una transición hacia meses más lluviosos, pero esto no demuestra su exactitud. No detectó cambios de ese tamaño en Q. Este cribado no es una prueba de rupturas de homogeneidad.

La disponibilidad no es uniforme entre meses calendario: el ciclo anual usa entre **39 y 42 años por mes**. El hecho de que varios vacíos afecten temporadas lluviosas puede sesgar la caracterización de extremos; por ello se reporta el número de años y no se asume que los faltantes sean aleatorios.

## 3. Estadística descriptiva

Las cifras siguientes utilizan los mismos 485 meses válidos de P y Q. La media de Q es la media aritmética de los promedios mensuales, no el promedio de todos los días ponderado por duración del mes.

| Estadístico | P (mm/mes) | Q (m³/s) | R (mm/mes) |
|---|---:|---:|---:|
| Media | 168,20 | 98,70 | 92,82 |
| Mediana | 168,47 | 85,55 | 81,40 |
| Desviación estándar muestral | 74,54 | 64,35 | 60,63 |
| Mínimo | 24,89 | 18,37 | 17,59 |
| Máximo | 407,57 | 508,77 | 471,45 |
| Cuartil 25 | 107,29 | 49,16 | 46,55 |
| Cuartil 75 | 216,55 | 127,04 | 118,83 |

El Excel incluye rango, IQR y percentiles 5, 10, 90 y 95. Se empleó desviación muestral (`ddof=1`) y percentiles con interpolación lineal. Los histogramas usan intervalos Freedman–Diaconis y porcentaje de meses. No hay meses completos con P o Q iguales a cero, aunque sí hay días sin lluvia.

En P, media y mediana son cercanas. En Q la media supera la mediana en unos **13,16 m³/s**, y la asimetría es **1,70**: los meses de caudal alto elevan el promedio. La mediana describe mejor el centro resistente a esos extremos, aunque una condición típica depende también del mes calendario. La dispersión de estas tablas no es un intervalo de confianza ni una cuantificación de errores de medición.

## 4. Lectura cronológica y revisión de extremos

Las figuras 1 y 5 muestran alternancia estacional y diferencias apreciables entre años. El periodo de finales de 2010 destaca por caudales persistentemente altos: **508,77 m³/s en noviembre y 439,72 m³/s en diciembre**. No corresponde a un único día alto: los 30 caudales diarios de noviembre van de **262,0 a 880,2 m³/s**, con mediana **514,75 m³/s**. Ese mes registra además **396,03 mm** de lluvia. Su coherencia interna respalda conservarlo, pero no verifica de forma independiente la medición ni permite atribuir el episodio a ENSO.

El máximo mensual de P es **octubre de 2022, 407,57 mm**, y su mínimo es **agosto de 1982, 24,89 mm**. El mínimo de Q es **julio de 1992, 18,37 m³/s**. Los mínimos de precipitación y caudal de todo el registro no coinciden; no debe calcularse un desfase usando esos extremos de años diferentes.

La figura 6 muestra ventanas de aproximadamente un año alrededor de los extremos de ambas variables. El periodo posterior al caudal mínimo de julio de 1992 presenta dos meses totalmente ausentes, por lo que no se puede describir su recuperación inmediata. Se observan agrupaciones de meses de Q bajo, por ejemplo en 2015–2016, pero no se ha aplicado una definición formal de sequía ni una prueba de tendencia.

No hay fundamento en estas gráficas para afirmar un aumento o disminución sostenido del caudal a largo plazo. Eso requiere los análisis de tendencias, dependencia temporal y homogeneidad del punto 3.

## 5. Hipótesis inicial del régimen

La climatología exploratoria (figura 4) muestra **dos máximos locales de lluvia**, en **abril (240,16 mm)** y **octubre (255,03 mm)**, separados por un mínimo en **julio (89,99 mm)**. Por máximo local se entiende un valor mayor que el de sus dos meses vecinos en el ciclo anual. El máximo de octubre equivale a unas **2,83 veces** la media de julio. Esta evidencia sugiere inicialmente un **régimen pluvial bimodal**, pendiente de comprobar su estabilidad entre años y subperiodos.

El caudal presenta máximos locales en **mayo (131,62 m³/s)** y **noviembre (157,01 m³/s)**, un mes después de cada pico de P; el mínimo ocurre en **agosto (46,85 m³/s)**. Este es un desfase de picos climatológicos a resolución mensual, no una estimación del tiempo de viaje del agua ni un resultado de correlación con rezagos.

El [POMCA del río La Vieja, capítulo 3, Clima](https://www.cvc.gov.co/sites/default/files/Planes_y_Programas/Planes_de_Ordenacion_y_Manejo_de_Cuencas_Hidrografica/La%20Vieja%20-%20POMCA%20en%20Ajuste/Fase%20Diagnostico/3_CapituloI_Diagnostico_Clima.pdf), estudio 2017 alojado por CVC, sección 3.3 (p. impresa 20; PDF 24) relaciona las dos temporadas lluviosas regionales con la migración de la ZCIT. Su tabla 3.8 (p. impresa 36; PDF 40) también muestra dos máximos de precipitación media en abril y octubre. Es evidencia regional compatible con nuestro ciclo; no valida directamente CHIRPS, pues las fuentes, periodos y delimitación pueden diferir.

**Hipótesis a contrastar:** el ciclo de lluvia regional aporta dos temporadas de recarga y la respuesta de la cuenca prolonga la salida por el río hacia los meses siguientes. El almacenamiento en suelo/subsuelo es un mecanismo posible, no demostrado. La agregación mensual, el reparto espacial de lluvia, las extracciones y la regulación son explicaciones alternativas o adicionales. Para distinguirlas se necesitan antecedentes locales, comparación de productos y análisis de rezagos con series originales y anomalías.

En **44 meses** R supera P. No se etiquetan como errores: pueden intervenir agua almacenada, intercambios, sesgos de precipitación/caudal o incertidumbre del área. La razón entre sumas de R y P en los 485 meses pareados es **0,552**, pero no es un balance cerrado de los 42 años, pues omite meses. Tampoco se interpreta P−R como evapotranspiración.

## 6. Comprobaciones y sensibilidad

La agregación se verificó con sumas independientes de Python, además de pandas:

- **Enero de 1981:** 31 días; P = **50,945 mm**; suma de Q diario = **1829,3**; Q medio = **59,0097 m³/s**; volumen = **158.051.520 m³**; R = **56,5037 mm**.
- **Febrero de 1992:** 29 días; P = **111,351 mm**; Q medio = **42,8724 m³/s**; R = **38,4032 mm**. Se verificó explícitamente el año bisiesto.

Los cálculos coinciden con las series exportadas. El uso de una suma de caudales diarios se entiende como un paso intermedio: para obtener volumen se multiplica por 86.400 segundos por día.

Como sensibilidad, permitir meses de Q con al menos 90 % de días elevaría la muestra a **494 meses** y la media a **100,91 m³/s**, frente a 98,70 con el criterio estricto (cambio de alrededor del **2,24 %**). Esto no valida los días faltantes ni justifica completar P. Se conserva el criterio del 100 % como análisis principal.

## 7. Alcance y próximos datos necesarios

Se completó la primera exploración de P/Q y la conversión a R, con figuras, estadísticas, auditoría y una hipótesis inicial. Quedan pendientes la precipitación IMERG real (el intento de acceso requirió autenticación Earthdata), la temperatura media mensual, la comparación de fuentes y el desarrollo completo de la climatología del apartado 1.5. No se sustituyeron descargas fallidas por datos simulados.

La lámina R depende del área elegida. El cálculo geodésico previo del polígono produjo aproximadamente 2780,18 km², frente a 2797,19 en los atributos CAMELS: diferencia cercana al 0,61 %. Se mantiene por consistencia el área CAMELS y se deja pendiente el contraste cartográfico; usar el área geodésica elevaría R aproximadamente 0,61 %.

El grupo debe revisar las alertas con información de estación, leer las fuentes originales y decidir si conserva el criterio de completitud. El código permite regenerar los resultados sin alterar los datos originales.

## Reproducción y uso de IA

Ejecutar `python seleccion_cuenca/scripts/08_exploracion_mensual_la_vieja.py`. Requiere el ZIP original guardado en `seleccion_cuenca/datos/`, Python, pandas, numpy, matplotlib y openpyxl. El informe visual se genera con `scripts/09_informe_exploracion.py`. Las figuras se guardan en PNG y PDF, y las tablas en CSV y Excel.

La IA apoyó la programación, el control aritmético, la lectura del capítulo regional y la redacción de esta interpretación preliminar. Se verificaron fechas, completitud, conservación de vacíos, conversiones de dos meses, coherencia entre R y Q y legibilidad de figuras. No se verificaron externamente los aforos ni los registros individuales de estaciones meteorológicas. Las hipótesis físicas permanecen sujetas a revisión del grupo.
