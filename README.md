# Informes de Hidrología

Los dos programas están en **[Códigos python](HIDROLOG%C3%8DA%202.0/C%C3%B3digos%20python/)**:

- **[Generar informe interactivo.py](HIDROLOG%C3%8DA%202.0/C%C3%B3digos%20python/Generar%20informe%20interactivo.py)**: ejecutar con Python para generar el HTML completo.
- **[Generar informe PDF.py](HIDROLOG%C3%8DA%202.0/C%C3%B3digos%20python/Generar%20informe%20PDF.py)**: ejecutar con Python para generar el PDF completo de 486 páginas. Instala PyMuPDF si falta.

En VS Code, abrir el archivo elegido y pulsar **Ejecutar archivo de Python**.
También se puede ejecutar desde la terminal, en la carpeta principal:

```powershell
python "HIDROLOGÍA 2.0/Códigos python/Generar informe interactivo.py"
python "HIDROLOGÍA 2.0/Códigos python/Generar informe PDF.py"
```

Los resultados quedan en **HIDROLOGÍA 2.0/seleccion_cuenca/salida_informes/**.
Los informes ya hechos están en la raíz: `Informe_Hidrologia_interactivo.html`
y `Informe_Hidrologia_actualizado_1_5.pdf`.

Se necesita Python y el proyecto completo, incluidas las fuentes descargadas mediante
Git LFS. No basta copiar los dos programas fuera del proyecto.
La generación reconstruye la edición publicada desde fuentes verificadas;
no recalcula los análisis científicos desde observaciones brutas.

Más detalles en [README_INFORMES.md](README_INFORMES.md).
