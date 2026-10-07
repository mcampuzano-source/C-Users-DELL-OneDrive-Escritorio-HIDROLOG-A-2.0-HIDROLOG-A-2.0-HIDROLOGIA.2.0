# Continuidad del trabajo — 6 de octubre de 2026

Base: GitHub commit e0efb8edf2104605d39bb5324b0f5f638b35103e.
Carpeta activa: revision_github_2026-10-05.

Solicitud del usuario: incorporar cada nuevo avance tanto en informe_actualizado.pdf como en informe_interactivo.html. Verificar ambos antes de entregar.

Corrección de visualización: integrar dispersiones_requeridas.png y tendencias_mensuales.png como data URI en el HTML. El PDF ya contiene los tres diagramas de dispersión en la página 23; se verificó visualmente y se conserva sin recalcular ni modificar resultados.

Ejecutar integrar_imagenes_html.py después de regenerar el HTML para evitar referencias a imágenes locales ausentes.

Pendiente: reconciliar los textos históricos de IMERG/temperatura con los apartados actualizados. No mezclar promedio IMERG de caja con promedio del polígono ni MSWX con ERA5-Land. Lluvia local tiene 22 meses comunes; IMERG–Q tiene 285 meses. No atribuir automáticamente las estadísticas históricas a la nueva serie poligonal sin comprobar su procedencia.


## Actualizacion del apartado 2.1
PDF activo: informe_actualizado_2_1.pdf (el PDF anterior esta abierto y Windows impide sobrescribirlo). HTML activo: informe_interactivo.html. Ambos sincronizados. Recalculado con IMERG poligonal y 14 meses locales de cobertura completa. Incluye diagramas, errores, Pearson/Spearman, influencia, rezagos calendario 0-3 y anomalias IMERG-Q/R con climatologia comun 285 meses (1998-2022). Fuente editable: proyecto/la_vieja/documentos/latex/informe_ordenado.tex. Script: completar_21.py. PDF compilado con Tectonic y verificado visualmente, paginas 23-25. Seis graficos Plotly nuevos; comprobados sintaxis JavaScript y argumentos, no una sesion real de navegador (no disponible). No afirmar cierre total: faltan datos locales para una climatologia y anomalias defendibles. Integrar posteriormente climatologia en 1.5 y 3.2. No usar estadisticas historicas de caja o meses locales parciales como resultados actuales.
