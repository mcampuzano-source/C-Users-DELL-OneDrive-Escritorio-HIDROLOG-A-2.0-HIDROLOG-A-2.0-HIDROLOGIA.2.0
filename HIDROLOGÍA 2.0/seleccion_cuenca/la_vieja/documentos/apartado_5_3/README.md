# Robustez 5.3

Reproducción: scripts 48_calcular_robustez_5_3.py, 49_presentar_robustez_5_3.py y 50_integrar_5_3.py.
La inferencia es Pearson bilateral con n efectivo AR(1) anual y FDR BY global.
BH es sensibilidad; Spearman y los subperiodos son descriptivos.
Se conserva precisión completa en los NetCDF; el visor redondea a 0,001.
Excel es una exportación de diagnósticos calculados en Python, no un motor de inferencia.
Datos originales: imerg_poligono/series_alineadas.csv y datos/clima_global_5_1.
Ver metodologia.md, resultados.json y verificacion_reproduccion_5_2.csv.
No ejecutar el script 47 como último paso: genera la versión histórica sin 5.3.

Excel: 51_excel_robustez.mjs con @oai/artifact-tool. Verificar visor: 52_verificar_html_5_3.mjs.
