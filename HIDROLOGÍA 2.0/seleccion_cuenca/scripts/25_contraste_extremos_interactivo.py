"""Incorpora al HTML el contraste breve de extremos sin alterar gráficos."""
from pathlib import Path
import re
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'la_vieja' / 'documentos'


def main():
    stats = pd.read_csv(DOC / 'imerg_poligono' / 'estadisticos_periodo_comun.csv')
    table = stats[['variable', 'unidad', 'mes_minimo', 'minimo', 'mes_maximo', 'maximo']].rename(columns={
        'variable': 'Variable', 'unidad': 'Unidad', 'mes_minimo': 'Mes mínimo',
        'minimo': 'Mínimo', 'mes_maximo': 'Mes máximo', 'maximo': 'Máximo'})
    paragraphs = [
        'Las fechas de la tabla corresponden a los mínimos y máximos de los mismos 285 meses completos de 1998–2022. '
        'Al ubicarlas en las cinco series cronológicas del punto 1.2 y revisar sus meses vecinos, se observa coherencia general: '
        'en noviembre de 2010 coinciden los máximos de IMERG, caudal y escorrentía, con CHIRPS también muy alto '
        '(396,03 mm/mes) y caudal elevado en diciembre. Noviembre de 1999 presenta caudal extremo después de octubre lluvioso; '
        'en octubre de 2022 la lluvia máxima de CHIRPS coincide con IMERG alto y el caudal sigue aumentando en noviembre. '
        'Estas secuencias son compatibles con episodios húmedos y almacenamiento de agua en la cuenca, sin demostrar por sí solas una causa específica.',
        'Los valores bajos también muestran relaciones plausibles: agosto de 2001 combina poca lluvia y caudal bajo; '
        'enero–febrero de 1998 reúne poca lluvia, caudal bajo y temperatura alta en enero. El mínimo de caudal de septiembre de 2019 '
        'sigue a agosto seco, con recuperación del caudal en octubre. La temperatura mínima de enero de 2000 sucede después de '
        'los meses lluviosos de finales de 1999, con caudal todavía elevado. Diciembre de 2015 requiere revisión: '
        'IMERG registra 60,83 mm/mes frente a 170,66 en CHIRPS, aunque coinciden caudal bajo y temperatura alta. '
        'La secuencia puede ser plausible, pero la discrepancia entre productos no permite confirmar un error ni validar el mínimo '
        'sin información independiente. Q y R no son evidencias independientes porque R deriva de Q, y los días de cada mes '
        'pueden cambiar la fecha de su mínimo. No se descarta ningún dato. El máximo del registro completo de IMERG '
        '(noviembre de 2008: 447,12 mm/mes) queda fuera de la muestra común por ausencia de CHIRPS y Q; '
        'los extremos históricos anteriores a 1998 se mantienen separados y requieren su propio contraste.'
    ]
    path = DOC / 'informe_interactivo.html'
    text = path.read_text(encoding='utf-8')
    start_marker, end_marker = '<!-- CONTRASTE_EXTREMOS_INICIO -->', '<!-- CONTRASTE_EXTREMOS_FIN -->'
    original = re.sub(re.escape(start_marker)+'.*?'+re.escape(end_marker), '', text, flags=re.S)
    block = start_marker+'<div id="contraste-extremos-mensuales"><h3>Meses extremos: coherencia y plausibilidad</h3>'
    block += '<p>Muestra común: 285 meses; fechas en formato año-mes y unidades propias de cada variable.</p>'
    block += '<div style="overflow:auto">'+table.to_html(index=False, float_format=lambda v: f'{v:.2f}')+'</div>'
    block += ''.join('<p>'+p+'</p>' for p in paragraphs)+'</div>'+end_marker
    section = original.index('<section class="panel" id="imerg-poligono-estadisticos">')
    end = original.index('</section>', section)
    updated = original[:end]+block+original[end:]
    assert re.sub(re.escape(start_marker)+'.*?'+re.escape(end_marker), '', updated, flags=re.S) == original
    path.write_text(updated, encoding='utf-8')
    print('Tabla y dos párrafos de contraste incorporados; contenido previo conservado.')


if __name__ == '__main__':
    main()
