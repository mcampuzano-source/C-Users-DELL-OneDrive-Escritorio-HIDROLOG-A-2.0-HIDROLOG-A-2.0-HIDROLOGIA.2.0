# Apartado 2.2: modelos con IMERG y CHIRPS

Actualización: 6 de octubre de 2026. Se conserva el desarrollo del punto 1.3 presente en el repositorio al iniciar la publicación.

Se evalúan lluvia local desde IMERG/CHIRPS y caudal desde ambos productos, con lluvia local–caudal como ejercicio exploratorio. Los informes incluyen ecuaciones, parámetros, unidades, supuestos, rangos y límites de interpretación.

## Muestras y evaluación

- Lluvia local: 14 meses con todos los intervalos esperados; no los 22 acumulados no vacíos. Diagnóstico temporal corto: siete meses de 2018 para ajustar y siete de 2019 para comparar.
- Caudal: 274 fechas comunes con lluvia actual y del mes anterior disponibles para ambas fuentes. Desarrollo: 206 meses hasta 2016. Tres validaciones por bloques aportan 105 estimaciones sin utilizar el futuro para ajustar.
- Reserva del 2.3: 68 meses de 2017–2022, **sin evaluar**. Selección y parámetros de caudal no usan resultados de esa reserva.

Los candidatos comparados son media, climatología mensual, recta contemporánea, recta con un mes de rezago, dos lluvias (actual y anterior) y raíz de precipitación. Se aplica `max(0, estimación)` para evitar valores negativos. El rango superior no se recorta.

Para caudal se selecciona lluvia actual y antecedente: RMSE de desarrollo 56,43 m³/s con IMERG y 63,87 con CHIRPS. La ventaja de IMERG no implica menor sesgo ni mejor reproducción de extremos; ambos presentan errores persistentes. Las calibraciones de lluvia local son exploratorias y no validan lluvia verdadera de toda la cuenca.

## Reproducir ambos informes

Desde la carpeta `HIDROLOGÍA 2.0`:

```powershell
python seleccion_cuenca/scripts/35_reproducir_puntos_2_1_2_2.py
```

Se necesitan Python con NumPy, pandas y Matplotlib, y Tectonic en PATH o en `seleccion_cuenca/herramientas/tectonic/tectonic.exe`. Se puede indicar otro ejecutable con `--tectonic RUTA`.

El script 35 ejecuta 32 (que llama a 31) y 34 (que llama a 33), integra imágenes locales en el HTML, compila `latex/informe_ordenado.tex` y actualiza `informe_actualizado.pdf`. Si se regeneran documentos con scripts anteriores, ejecutar 35 **al final** para reincorporar los puntos 2.1 y 2.2.

Los CSV y JSON conservan muestras, parámetros, métricas por bloque y estimaciones de desarrollo. No se generan predicciones de la reserva final. Los gráficos estáticos e interactivos usan esos mismos resultados. La comparación de anomalías que incluye lluvia local sigue condicionada a contar con una climatología local adecuada.


Actualizacion posterior: los 68 meses reservados ya se evaluaron sin reajuste en [2.3](../apartado_2_3/README.md). Los metadatos del 2.2 se conservan intactos como registro de las decisiones previas a abrir esa prueba.
