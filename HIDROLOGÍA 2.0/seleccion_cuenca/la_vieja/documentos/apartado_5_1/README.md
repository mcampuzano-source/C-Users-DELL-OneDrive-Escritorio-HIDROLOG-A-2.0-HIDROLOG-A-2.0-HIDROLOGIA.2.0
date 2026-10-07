# Apartado 5.1

Selecci?n de ERSSTv5 SST y NCEP/NCAR R1 SLP/Z500, con presi?n superficial auxiliar. Cada campo dispone de 504 meses 1981-2022. La muestra principal de cuenca tiene 285 meses completos 1998-2022.

Los NetCDF de anomal?as contienen climatolog?a, conteos y m?scara mensual; no contienen correlaciones. ERA5 se ha revisado documentalmente y no se ha descargado.

Reproducci?n: ejecutar 41_descargar_campos_globales.py. Si NOAA NCSS no permite crear recortes SST, ejecutar 41b_recuperar_sst_opendap.py y despu?s 41. Ejecutar 42_preparar_punto_5_1.py y 40_integrar_pdf_punto3.py para preparar e integrar los informes. El contexto acad?mico se reproduce con 43_redactar_contexto_academico.py y 40.

Cada fragmento mantiene su solicitud y huella SHA-256. Los datos originales est?n en datos/clima_global_5_1. Los metadatos, conteos y verificaciones se conservan en resultados.json e inventario_campos.csv.
