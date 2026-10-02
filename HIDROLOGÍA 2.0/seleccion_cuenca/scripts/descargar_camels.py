import concurrent.futures
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'datos'
OUT.mkdir(exist_ok=True)
URL = 'https://zenodo.org/api/records/18794895'
with urllib.request.urlopen(URL, timeout=60) as response:
    metadata = json.load(response)
(OUT / 'zenodo_18794895.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
prefixes = ('00_', '01_', '02_', '03_', '04_', '06_', '10_')

def download(item):
    path = OUT / item['key']
    if not path.exists() or path.stat().st_size != item['size']:
        with urllib.request.urlopen(item['links']['self'], timeout=180) as response, path.open('wb') as out:
            while chunk := response.read(1024 * 1024):
                out.write(chunk)
    return f'{path.name}: {path.stat().st_size} bytes'

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(download, [f for f in metadata['files'] if f['key'].startswith(prefixes)]):
            print(result, flush=True)
