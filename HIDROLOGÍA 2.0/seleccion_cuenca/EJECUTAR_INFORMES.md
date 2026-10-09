# Ejecutar los informes completos

Las entradas principales, fáciles de localizar, son los dos archivos de la carpeta
**HIDROLOGÍA 2.0/Códigos python**. Cada uno genera directamente su
informe; no es necesario recorrer los scripts numerados. La entrada PDF instala
PyMuPDF automáticamente si falta.

`Codigo_desde_el_inicio.html` es una vista de las fuentes, no un programa Python.
Las entradas ejecutables están en `scripts/`:

- `ejecutar_informes.py`: reconstruye ambos informes.
- `generar_informe_interactivo.py`: reconstruye el HTML con todo su contenido y el selector de los cuatro casos.
- `generar_informe_pdf.py`: reconstruye el PDF publicado completo, de 486 páginas.

Desde esta carpeta, ejecutar:

```powershell
python -m pip install -r requirements_informes.txt
python scripts/ejecutar_informes.py
```

También se puede ejecutar un script por su ruta absoluta desde otra carpeta.
Las rutas de entrada se resuelven a partir del código, no del directorio de la terminal.
La salida predeterminada es `salida_informes/`, con HTML, PDF y un JSON de verificación.

Para generar solo un informe:

```powershell
python scripts/generar_informe_interactivo.py
python scripts/generar_informe_pdf.py
```

Para escoger una carpeta de salida o actualizar las copias principales:

```powershell
python scripts/ejecutar_informes.py --salida "C:\Users\Marcos\Documents\Informes_generados"
python scripts/ejecutar_informes.py --publicar
```

Sin `--publicar` no se modifican los informes principales. Con esa opción se guardan
copias previas en una carpeta temporal y se actualizan las versiones principales.
Los resultados generados no necesitan subirse como duplicados a GitHub.

## Fuentes y alcance

`fuentes_informes/` contiene el HTML completo de la edición base, su PDF de 480 páginas,
los dos bloques HTML del control 1.4, cuatro páginas de contraste y dos páginas del
registro de anomalías. El manifiesto identifica la edición y las huellas SHA-256.
Estas fuentes son necesarias: no son los respaldos temporales excluidos anteriormente.

Al descargar o clonar el repositorio, ejecutar `git lfs pull` para obtener el PDF base
completo. Un archivo de texto de Git LFS no es un PDF; el programa lo detecta por su huella.

Este código **reconstruye la edición publicada**, conservando los análisis y las
interpretaciones recibidas. **No recalcula todo el estudio desde observaciones brutas**.
Los scripts históricos incluyen los análisis científicos, requieren otras dependencias,
datos y, en algunos casos, servicios externos. Ejecutarlos todos en orden numérico
puede sustituir secciones por versiones anteriores. Los scripts 84 y 85 son históricos;
la entrada 86 ahora remite al generador portable.

Se verifica la integridad de las fuentes, la conservación del HTML original, los cuatro
casos del selector, la portada y el texto científico de las 478 páginas originales
posteriores al índice, además de la paginación final y los marcadores del PDF.

El visor de los cuatro casos incluye Plotly. Otras secciones originales del informe
pueden requerir sus bibliotecas o recursos externos; conservar el contenido no implica
que todos los servicios externos estén disponibles sin conexión.

Para renovar las vistas de código:

```powershell
python scripts/24_actualizar_codigo_completo.py
python scripts/documentar_codigo_pdf.py
```
