"""Amplía el inciso 1.3 sin modificar series, tablas previas ni figuras."""
from pathlib import Path
import re
import pandas as pd

DOC = Path(__file__).resolve().parents[1] / 'la_vieja' / 'documentos'
OUT = DOC / 'imerg_poligono'
KEYS = {
    'P_CHIRPS_mm': ('CHIRPS', 'mm/mes'),
    'P_IMERG_poligono_mm': ('IMERG polígono', 'mm/mes'),
    'Q_m3_s': ('Caudal Q', 'm³/s'),
    'R_mm': ('Escorrentía R', 'mm/mes'),
    'Tmedia_ERA5_Land_C': ('ERA5-Land Tmedia', '°C'),
}


def main():
    common = pd.read_csv(OUT / 'meses_comunes_285.csv', parse_dates=['mes'])
    full = pd.read_csv(OUT / 'series_alineadas.csv', parse_dates=['mes'])
    rows, paragraphs = [], []
    for key, (label, unit) in KEYS.items():
        s = common[key]
        assert len(s) == 285 and s.notna().all()
        q1, q3 = s.quantile([.25, .75], interpolation='linear')
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        below, above = int((s < lower).sum()), int((s > upper).sum())
        skew = float(s.skew())
        rows.append(dict(variable=label, asimetria=skew, limite_inferior=lower,
                         limite_superior=upper, fuera_inferior=below, fuera_superior=above,
                         fuera_total=below+above, porcentaje_fuera=100*(below+above)/len(s)))
        direction = 'hacia valores altos' if skew > 0 else 'hacia valores bajos'
        shape = ('La asimetría es pequeña; esto no demuestra normalidad ni ausencia de colas.'
                 if abs(skew) < .5 else
                 f'La distribución presenta asimetría {direction}; los extremos de ese lado influyen en la media.')
        typical = ('La mediana describe mejor el centro resistente a meses extremos; la media conserva su utilidad para el promedio del registro.'
                   if key in ('Q_m3_s', 'R_mm') else
                   'Media y mediana próximas describen un centro parecido, pero no permiten por sí solas afirmar simetría.')
        p5, p95 = s.quantile([.05, .95], interpolation='linear')
        paragraphs.append(f'{label}: media {s.mean():.2f} y mediana {s.median():.2f} {unit}; '
                          f'desviación estándar muestral {s.std(ddof=1):.2f} {unit}. '
                          f'El 50% central se encuentra entre {q1:.2f} y {q3:.2f} {unit} '
                          f'(IQR {iqr:.2f} {unit}); P5 y P95 son {p5:.2f} y {p95:.2f} {unit}, '
                          'y delimitan aproximadamente el 90% central, con interpolación. '
                          f'Asimetría ajustada {skew:.3f}. {shape} {typical} '
                          f'Hay {below} meses por debajo y {above} por encima de los límites de la caja '
                          f'({below+above} en total; {100*(below+above)/len(s):.2f}%). '
                          'Son observaciones señaladas por un criterio estadístico, no errores demostrados; se conservan todas.')
    metrics = pd.DataFrame(rows)
    metrics.to_csv(OUT / 'asimetria_y_cajas_285.csv', index=False)
    coverage = []
    for key, (label, unit) in KEYS.items():
        # IMERG comienza en 1998; no confundir meses previos con faltantes internos.
        frame = full.loc[full.mes >= '1998-01-01'] if key == 'P_IMERG_poligono_mm' else full
        coverage.append(dict(variable=label, meses_periodo=len(frame), validos=int(frame[key].notna().sum()),
                             faltantes=int(frame[key].isna().sum()), ceros_validos=int((frame[key].dropna()==0).sum())))
    coverage = pd.DataFrame(coverage)
    coverage.to_csv(OUT / 'ceros_y_faltantes_por_fuente.csv', index=False)
    intro = ('Descripción ampliada del segundo inciso, sobre los mismos 285 meses completos de 1998–2022. '
             'La asimetría se calcula con el coeficiente ajustado de Fisher–Pearson '
             '(pandas Series.skew, sin unidades): un signo positivo indica cola hacia valores altos y uno negativo hacia valores bajos. '
             'Los límites son Q1 − 1,5 IQR y Q3 + 1,5 IQR; los conteos usan desigualdades estrictas y percentiles lineales tipo 7. '
             'Estos límites son umbrales de detección: los bigotes terminan en las observaciones más extremas que permanecen dentro de ellos. '
             'No se aplica una prueba de normalidad ni se elimina ningún valor.')
    conclusion = ('Comparación de precipitaciones: en la muestra común, IMERG tiene un centro más alto '
                  '(media 216,55 frente a 170,50 mm/mes), pero menor dispersión absoluta '
                  '(desviación estándar 71,79 frente a 76,43 mm/mes; IQR 101,98 frente a 114,74 mm/mes). '
                  'Por ello, mayor precipitación media no implica mayor variabilidad. Las tablas permiten comparar las colas '
                  'y los porcentajes fuera de las cajas con idéntico número de meses. Las diferencias son entre productos '
                  'y no demuestran cuál es más exacto. R deriva de Q: su relación no es evidencia independiente; '
                  'la conversión mensual incorpora la duración de cada mes. La dispersión de temperatura se interpreta en °C; '
                  'no se usa un coeficiente de variación en Celsius porque su cero es convencional. '
                  'No se comparan directamente desviaciones estándar de variables con unidades diferentes.')
    missing = ('Ceros y ausencias: no hay valores iguales a cero en los registros válidos de estas cinco variables, '
               'ni faltantes en los 285 meses comunes. En las coberturas originales de 1981–2022, CHIRPS, Q y R '
               'tienen 19 meses ausentes cada uno; ERA5-Land tiene 504 meses válidos. IMERG tiene 300 meses válidos '
               'y ningún faltante en 1998–2022: los 204 meses anteriores están fuera de su cobertura utilizada. '
               'La intersección excluye 15 meses de 1998–2022 porque no todas las variables están disponibles. '
               'No se rellenan ausencias con cero. Una temperatura de 0 °C sería una temperatura válida, no ausencia. '
               'Estas distribuciones mezclan meses de distintas estaciones; no representan la variabilidad interanual '
               'de un mes calendario particular, que corresponde al punto 1.5. '
               'La coherencia cronológica y plausibilidad de los extremos sigue pendiente del tercer inciso.')
    assert coverage.faltantes.tolist() == [19, 0, 19, 19, 0]
    texts = [
        'En los 285 meses comunes de 1998–2022, CHIRPS, IMERG y temperatura presentan poca asimetría hacia valores altos, mientras que caudal y escorrentía muestran colas superiores más marcadas: sus meses extremos elevan la media por encima de la mediana. IMERG tiene mayor precipitación media que CHIRPS (216,55 frente a 170,50 mm/mes), pero menor dispersión (desviación estándar 71,79 frente a 76,43 mm/mes; IQR 101,98 frente a 114,74 mm/mes). Para caudal y escorrentía, la mediana representa mejor una condición típica resistente a extremos; las diferencias entre productos no demuestran cuál es más exacto.',
        'Con percentiles lineales tipo 7 y límites Q1 − 1,5 IQR y Q3 + 1,5 IQR, las cajas señalan 1 mes en CHIRPS, 1 en IMERG, 6 en caudal, 5 en escorrentía y 3 en temperatura fuera de esos límites; todos se conservan, pues ese criterio no demuestra errores. La asimetría ajustada de Fisher–Pearson y los conteos se presentan en las tablas. No hay ceros ni faltantes en la muestra común: los meses sin información se excluyeron, sin reemplazarlos por cero; 0 °C sería una temperatura válida. Las coberturas originales y sus faltantes se distinguen en la tabla por fuente. Estas distribuciones reúnen distintas estaciones del año y no sustituyen la climatología del punto 1.5; la coherencia temporal y plausibilidad de los extremos se revisará en el tercer inciso.',
    ]
    html = DOC / 'informe_interactivo.html'
    text = html.read_text(encoding='utf-8')
    text = re.sub(r'<!-- DISTRIBUCIONES_AMPLIADAS_INICIO -->.*?<!-- DISTRIBUCIONES_AMPLIADAS_FIN -->', '', text, flags=re.S)
    block = '<!-- DISTRIBUCIONES_AMPLIADAS_INICIO --><h3>Descripción ampliada: asimetría, dispersión, colas y ceros</h3>'
    block += ''.join('<p>'+p+'</p>' for p in texts)
    block += '<div style="overflow:auto">'+metrics.to_html(index=False, float_format=lambda v: f'{v:.3f}')+'</div>'
    block += '<h4>Cobertura, ceros y faltantes por fuente</h4><div style="overflow:auto">'+coverage.to_html(index=False)+'</div><!-- DISTRIBUCIONES_AMPLIADAS_FIN -->'
    start = text.index('<section class="panel" id="imerg-poligono-estadisticos">')
    end = text.index('</section>', start)
    html.write_text(text[:end]+block+text[end:], encoding='utf-8')
    def tex(t):
        return t.replace('−', '-').replace('–', '--').replace('%', r'\%').replace('³', r'$^3$').replace('°', r'$^\circ$')
    path = OUT / 'apartado_1_3.tex'
    original = re.sub(r'% DISTRIBUCIONES_AMPLIADAS_INICIO.*?% DISTRIBUCIONES_AMPLIADAS_FIN', '', path.read_text(encoding='utf-8'), flags=re.S)
    appendix = '\n% DISTRIBUCIONES_AMPLIADAS_INICIO\n\\subsubsection*{Descripción ampliada: asimetría, dispersión, colas y ceros}\n'
    appendix += '\n\n'.join(tex(p) for p in texts)+'\n'
    for columns in [['variable','asimetria','fuera_inferior','fuera_superior','porcentaje_fuera'],
                    ['variable','limite_inferior','limite_superior']]:
        appendix += '\\resizebox{\\linewidth}{!}{\n'+metrics[columns].to_latex(index=False, escape=True, float_format='%.3f')+'}\n'
    appendix += '\\resizebox{\\linewidth}{!}{\n'+coverage.to_latex(index=False, escape=True)+'}\n% DISTRIBUCIONES_AMPLIADAS_FIN\n'
    path.write_text(original+appendix, encoding='utf-8')
    print(metrics.to_string(index=False))
    print(coverage.to_string(index=False))


if __name__ == '__main__':
    main()
