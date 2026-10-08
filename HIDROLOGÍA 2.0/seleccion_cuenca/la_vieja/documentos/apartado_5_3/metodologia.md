# 5.3. Robustez

## Presentación, calendario y máscaras

Se conservan las doce combinaciones del 5.2: CHIRPS, IMERG y Q frente a SST, SLP y Z500 con rezago cero, y Q frente a los tres campos con rezago de un mes. No se busca un rezago óptimo. El campo antecede a la respuesta cuando ell=1. La muestra común contiene 285 meses completos de 1998-2022, con 22-25 pares de años por mes. Se exige n>=20 y varianza no nula para correlaciones completas; SST conserva su máscara terrestre y Z500 la máscara de presión superficial. Gris significa sin estimación válida, no correlación cero. Todos los mapas de correlación y sus diferencias usan escala divergente fija de -1 a 1; los mapas de n y n efectivo tienen escala secuencial y unidades de años. La estrella ubica aproximadamente La Vieja; la delimitación exacta se conserva en la cartografía de contexto del informe. Los mapas se calculan por celda, no entre celdas.

## Retiro de tendencias en ambas variables

Para cada mes calendario y celda se ajustan dos regresiones OLS, una para la respuesta de cuenca y otra para el campo global, contra el año real centrado, usando exactamente los mismos pares válidos. Se correlacionan sus residuos. Los huecos permanecen en sus años originales. Esto equivale a una correlación parcial lineal que controla el año, no a probar causalidad. Se comparan r de anomalías y r sin tendencia, sus diferencias espaciales y la correlación ponderada entre mapas. El ciclo mensual ya fue retirado por la climatología fija del 5.2. En subperiodos y exclusiones se reajustan las dos tendencias para evitar usar la tendencia de años retirados.

## Persistencia interanual e inferencia aproximada

La dependencia relevante se estima entre años consecutivos del mismo mes. No se trata enero y febrero como observaciones consecutivas ni se conectan artificialmente años separados por huecos. Por celda, rhoX y rhoY son las autocorrelaciones anuales de orden uno de los mismos pares; se requieren al menos diez pares anuales adyacentes. Se adopta la aproximación AR(1) n_eff = n(1-rhoX*rhoY)/(1+rhoX*rhoY), limitada a [3,n], basada en el tamaño efectivo para correlaciones de Bretherton et al. (1999). El límite superior evita aumentar la información por autocorrelación estimada negativa. La prueba bilateral usa t=|r| sqrt(df/(1-r²)), con df=n_eff-2 para anomalías y df=n_eff-3 al controlar el año. Con df<=1 no se emite p. Los p son aproximados: n corto, no normalidad, incertidumbre de rho y memoria de orden superior pueden afectar su calibración; no son una garantía exacta de cobertura o significancia.

## Una familia de pruebas y control FDR

La familia se fija antes de interpretar máximos: todas las celdas con p admisible, doce meses, doce combinaciones y ambas representaciones Pearson. Contiene 2,953,237 pruebas. No se reinicia el ajuste por mapa, mes o región ni se escoge ell por el mayor coeficiente. Se aplica Benjamini-Yekutieli (BY) con nivel 0,05, válido frente a dependencia arbitraria si los p individuales son válidos (Benjamini y Yekutieli, 2001). Benjamini-Hochberg (BH) se reporta solo como sensibilidad bajo independencia o dependencia positiva apropiada. El contraste p<0,05 sin corrección ilustra la diferencia entre significancia puntual y evidencia tras la búsqueda espacial; Wilks (2016) explica por qué los puntos aislados se sobreinterpretan. Spearman sin tendencia se conserva como contraste descriptivo y no amplía la familia inferencial. BY no repara p mal calibrados ni convierte una asociación en mecanismo causal.

## Subperiodos, años extremos y regiones coherentes

Los subperiodos se fijan en 1998-2009 y 2010-2022, sin elegir el corte por los resultados. Exigen al menos diez años por celda y usan tendencias propias; sus coeficientes se presentan como estabilidad descriptiva, sin pruebas FDR independientes. Al excluir cada año se reajusta OLS y se guarda el rango de r y el mayor cambio absoluto. También se retiran conjuntamente los dos años con mayor anomalía absoluta de la respuesta de cada mes, usando los mismos años para todo el campo; no se borran observaciones del archivo original. Esta comprobación detecta influencia, no demuestra que los extremos sean errores. Se contrasta CHIRPS con IMERG sobre iguales fechas y rejillas. Zaragoza tiene 14 meses completos, insuficientes para este contraste interanual.

## Criterio descriptivo de estabilidad

Se denomina estable una celda con |r sin tendencia|>=0,30, igual signo en ambos subperiodos y en todas las exclusiones individuales, y cambio máximo leave-one-year-out <=0,20. Los umbrales se declaran como reglas descriptivas, no como una segunda prueba o un intervalo de confianza. Una celda candidata requiere además q_BY<=0,05. Las áreas se ponderan por coseno de latitud sobre celdas con correlación completa válida. Se reporta el mayor componente contiguo de cuatro vecinos, con continuidad de longitud en la costura global, para evitar interpretar píxeles aislados. Las tres regiones SST (Niño 3.4, Atlántico tropical norte y Caribe) estaban definidas en el 5.2; aquí sus medias de coeficientes son diagnósticos de extensión regional y no la correlación de un índice espacial.

## Resultados de la muestra y alcance

La mediana espacial de n efectivo por mapa varía entre 21.1 y 25.0 años; el mínimo de una celda admisible es 12.4. El cambio espacial medio |r sin tendencia-r original| varía de 0.007 a 0.208. Los campos no deben tratarse como 2,953,237 observaciones independientes. El criterio conjunto deja celdas candidatas en 15 de los 144 mapas sin tendencia. La mayor fracción se encuentra en Q_sst_l0, Feb: 3.23% del dominio válido ponderado y 244 celdas; su mayor componente contiguo contiene 213 celdas. Estos máximos describen toda la búsqueda ya corregida, no una selección de rezago. La tabla y el atlas permiten verificar extensión, signo y continuidad; la explicación física se desarrollará en 5.4.

## Sensibilidad a la fuente y límites de interpretación

La correlación espacial ponderada entre los mapas CHIRPS e IMERG sin tendencia varía de 0.44 a 0.98; sus diferencias absolutas medias van de 0.060 a 0.210. Es un acuerdo de patrones de dos productos espaciales; no valida ninguno contra una verdad independiente ni sustituye la lluvia local. El caudal integra almacenamiento, regulación y respuesta de cuenca: una región climática asociada no identifica por sí sola un proceso. Las comparaciones entre subperiodos tienen 10-13 años, tendencias estimadas y baja potencia. Sin una validación adicional de memoria de orden superior, la inferencia se presenta como aproximada y condicionada al modelo AR(1). La conclusión física no se extrae de unos pocos coeficientes altos.

## Reproducibilidad y controles

El script 48 reproduce los cálculos y el 49 las figuras y documentos. Se conservan NetCDF con n, n efectivo, autocorrelaciones, p, q BH/BY, coeficientes y sensibilidad por celda; tablas CSV y Excel; metadatos, versiones y huellas SHA-256. Se comprueba OLS con años reales y faltantes contra mínimos cuadrados independientes, autocorrelación sin conectar huecos, continuidad de componentes en longitud y reproducción de los 144 mapas Pearson del 5.2 a precisión numérica. El visor usa rejillas nativas y redondea coeficientes a 0,001; no redondea datos para los cálculos. No se descargaron ni rellenaron nuevas observaciones. La IA apoyó programación y redacción; el grupo debe verificar decisiones y explicar los resultados en la defensa.

## Referencias

Bretherton et al. (1999). The Effective Number of Spatial Degrees of Freedom of a Time-Varying Field. Journal of Climate, 12, 1990-2009. Apéndice A: tamaño efectivo para correlaciones. https://journals.ametsoc.org/abstract/journals/clim/12/7/1520-0442_1999_012_1990_tenosd_2.0.co_2.xml

Benjamini y Yekutieli (2001). The control of the false discovery rate in multiple testing under dependency. Annals of Statistics, 29, 1165-1188. https://www.math.tau.ac.il/~ybenja/depApr27.pdf

Wilks (2016). The Stippling Shows Statistically Significant Grid Points: How Research Results are Routinely Overstated and Overinterpreted, and What to Do about It. BAMS, 97, 2263-2273. https://doi.org/10.1175/BAMS-D-15-00267.1

SciPy. false_discovery_control: implementaciones BH y BY. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.false_discovery_control.html