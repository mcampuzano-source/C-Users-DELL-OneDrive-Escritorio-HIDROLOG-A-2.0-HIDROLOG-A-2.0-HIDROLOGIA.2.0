# 2.3. Evaluación fuera del periodo de ajuste

Prueba cronológica: enero de 2017–diciembre de 2022, 68 meses comunes. Los modelos y los referentes de media y climatología se mantienen congelados en sus parámetros de desarrollo, hasta 2016. No se reajustan ni se seleccionan alternativas con esta prueba.

La tabla general incluye sesgo estimado−observado, MAE, RMSE y NSE; se añaden resultados por año, mes calendario y condición de caudal, y residuos frente al tiempo, estimado y mes. El caudal alto se define con el percentil 75 del ajuste (141,54 m³/s). El remuestreo pareado usa bloques calendario de seis y doce meses; no meses sueltos independientes.

CHIRPS: RMSE 42,14, MAE 30,23 y sesgo +2,47 m³/s. IMERG: RMSE 43,77, MAE 34,49 y sesgo −10,06 m³/s. Climatología entrenada: RMSE 51,14 m³/s. La diferencia global es pequeña y sus intervalos aproximados incluyen cero. CHIRPS tiene menor error en el grupo de caudales altos; IMERG en los bajos-medios. Ambos subestiman los altos.

## Datos y limitaciones

- Se excluyen junio y julio de 2021 y marzo y abril de 2022 por falta de pares mensuales completos o de lluvia antecedente. Se conservan los huecos del calendario.
- Los catorce meses de lluvia local ya participaron en el desarrollo. No existe una nueva reserva independiente para validar las ecuaciones locales. `diagnostico_local_previo.csv` documenta el corte 2018→2019 ya usado en 2.2 y sus referencias sin corrección; no se presenta como una segunda prueba final.
- IMERG Final y CHIRPS incorporan información de estaciones. No se ha comprobado si Zaragoza participa en sus redes. La independencia temporal del ajuste no demuestra independencia de fuentes.
- Se evalúa estimación mensual retrospectiva: los modelos usan lluvia del mismo mes. No son pronósticos adelantados ni modelos de crecidas con conservación de masa.
- Los modelos del 2.2 no usan la reserva para ajustar o seleccionar, pero las series de ese periodo ya aparecieron en la exploración de 1.1 y 2.1. Es una evaluación temporal fuera del ajuste; no un experimento totalmente ciego.

## Reproducir

Desde `HIDROLOGÍA 2.0`:

```powershell
python seleccion_cuenca/scripts/37_reproducir_evaluacion_2_3.py
```

Se necesitan NumPy, pandas, Matplotlib y Tectonic. El compilador admite `--tectonic RUTA`. El script 37 llama al 36 y compila ambos informes; no vuelve a ejecutar el ajuste del 2.2. Si se regeneran 2.1 y 2.2 con el script 35, ejecutar 37 al final.

`resultados.json` registra las ecuaciones aplicadas, el hash SHA-256 del archivo de parámetros del 2.2, las exclusiones y resultados. Los CSV conservan estimaciones, métricas y diagnósticos; figuras y gráficos interactivos usan las mismas predicciones.
