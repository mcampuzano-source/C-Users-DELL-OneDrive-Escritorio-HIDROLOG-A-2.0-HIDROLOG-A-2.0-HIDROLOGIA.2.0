#!/usr/bin/env python3
"""
Python script for downloading data from the NASA CMR API

Requirements:
    > pip install earthaccess requests tqdm h5py

To run the script: `python download_files_GPM_3IMERGM_07.py`
"""

import os
from pathlib import Path
from threading import local
from urllib.parse import urlparse, unquote
import earthaccess
import h5py
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

CMR_BASE_URL = "https://cmr.earthdata.nasa.gov"

SHORT_NAME = "GPM_3IMERGM"
VERSION = "07"
FILTER_TEMPORAL = "1998-02-01T00:00:00Z,2022-12-31T23:59:59Z"
FILTER_BBOX = ""
FILTER_SEARCH = ""
FILTER_CLOUD_COVER_MIN = ""
FILTER_CLOUD_COVER_MAX = ""
DOWNLOAD_DIR = str(Path(__file__).resolve().parent / f"{SHORT_NAME}_{VERSION}")
MAX_WORKERS = 5  # Number of parallel downloads
SESSIONS = local()


def authenticated_session():
    if not hasattr(SESSIONS, "session"):
        SESSIONS.session = earthaccess.get_requests_https_session()
    return SESSIONS.session


def valid_hdf5(path):
    try:
        with h5py.File(path, "r") as data:
            if not all(name in data for name in ["Grid/precipitation", "Grid/lat", "Grid/lon"]):
                return False
            # Read the full precipitation array to detect truncation/corrupt chunks.
            data["Grid/precipitation"][:]
        return True
    except (OSError, ValueError, KeyError):
        return False


def query_cmr_granules(
    short_name: str,
    version: str,
    page_size: int = 2000,
    search_after: str | None = None,
    **extra_params,
):
    """
    Queries the CMR granules endpoint.

    Args:
        short_name: The short name of the collection
        version: The version of the collection
        page_size: The number of results per page (max is 2000)
        search_after: The pagination token for subsequent requests (optional, see https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#search-after for more details)
        **extra_params: Additional query parameters (e.g., temporal, bounding_box, etc.)

    Returns:
        tuple: (response object, list of granule items)
    """
    url = f"{CMR_BASE_URL}/search/granules.umm_json"

    params = {
        "short_name": short_name,
        "version": version,
        "page_size": page_size,
        **extra_params,  # Merge any additional parameters
    }

    headers = {"Accept": "application/json"}
    if search_after:
        headers["CMR-Search-After"] = search_after

    response = requests.get(url, params=params, headers=headers, timeout=60)

    try:
        response.raise_for_status()
    except requests.exceptions.HTTPError:
        print("Failed to fetch granules:", response.text)
        raise

    data = response.json()
    items = data.get("items", [])

    return response, items


def download_data_from_cmr(
    short_name: str, version: str, total_granules: int, page_size: int = 2000, **params
):
    """Fetches granules for a given collection from the CMR API, then downloads the data from the "GET DATA" URLs"""
    search_after_value: str | None = None
    all_download_urls = []
    granules_without_urls = 0

    # First pass: collect all download URLs
    print("Collecting download URLs...")
    with tqdm(total=total_granules, desc="Collecting URLs", unit="granule") as pbar:
        while True:
            # Use shared query function
            response, items = query_cmr_granules(
                short_name, version, page_size, search_after_value, **params
            )

            # Collect "GET DATA" URLs
            for item in items:
                pbar.update(1)  # Update progress for each granule processed
                download_urls = []
                for related_url in item.get("umm", {}).get("RelatedUrls", []):
                    url = related_url.get("URL", "")
                    parsed = urlparse(url)
                    if (related_url.get("Type") == "GET DATA"
                            and parsed.scheme == "https"
                            and parsed.hostname
                            and parsed.hostname.endswith(".nasa.gov")
                            and parsed.path.upper().endswith(".HDF5")):
                        download_urls.append(url)
                
                if download_urls:
                    # One archive link per monthly granule, not its alternative mirrors.
                    all_download_urls.append(download_urls[0])
                else:
                    granules_without_urls += 1

            # Read the next search-after value from response headers
            search_after_value = response.headers.get("CMR-Search-After")

            # There is no next search-after value, we've reached the end
            if not search_after_value:
                break

    all_download_urls = list(dict.fromkeys(all_download_urls))
    print(f"Found {len(all_download_urls)} files to download")
    if len(all_download_urls) != 299:
        raise RuntimeError("Se esperaban 299 archivos mensuales. Se detiene la descarga para revisar el catálogo.")
    if granules_without_urls > 0:
        print(f"⚠️ {granules_without_urls} granules have no download URLs")

    # Verify authenticated access before starting the batch.
    print("Comprobando el primer archivo con tu sesión Earthdata...")
    first_status, first_name = download_file(all_download_urls[0])
    if first_status == "failed":
        raise RuntimeError("Falló la prueba de acceso. No se inició la descarga masiva.")
    print(f"Prueba correcta: {first_name}")
    # Second pass: download all files in parallel
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0
    
    with tqdm(total=len(all_download_urls), desc="Downloading files", unit="file") as pbar:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit all download tasks at once
            future_to_url = {executor.submit(download_file, url): url for url in all_download_urls}
            
            # Process completed downloads as they finish
            for future in as_completed(future_to_url):
                status, filename = future.result()
                if status == "success":
                    downloaded_count += 1
                    pbar.set_description(f"Downloaded: {filename}")
                elif status == "skipped":
                    skipped_count += 1
                    pbar.set_description(f"Skipped: {filename}")
                else:  # failed
                    failed_count += 1
                    print(f"Failed: {filename}")
                
                pbar.update(1)

    print(f"Downloaded: {downloaded_count} files")
    if skipped_count > 0:
        print(f"Skipped: {skipped_count} files (already exist)")
    if failed_count > 0:
        print(f"Failed: {failed_count} files")
        raise RuntimeError("Hay descargas pendientes. Vuelve a ejecutar el script para reintentarlas.")


def download_file(url: str):
    """Download a single file and return (success, skipped, failed) status and filename"""
    filename = Path(unquote(urlparse(url).path)).name
    local_filename = os.path.join(DOWNLOAD_DIR, filename)
    partial_filename = local_filename + ".part"
    if os.path.exists(local_filename):
        if valid_hdf5(local_filename):
            return "skipped", filename
        print(f"Archivo existente no válido: {filename}; se conserva y se detiene para revisarlo.")
        return "failed", filename

    try:
        with authenticated_session().get(url, stream=True, timeout=(30, 120)) as r:
            r.raise_for_status()
            expected_size = r.headers.get("Content-Length")
            with open(partial_filename, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
        if expected_size and os.path.getsize(partial_filename) != int(expected_size):
            raise ValueError("La descarga está incompleta")
        if not valid_hdf5(partial_filename):
            raise ValueError("El archivo recibido no es un HDF5 IMERG válido")
        os.replace(partial_filename, local_filename)
        return "success", filename
    except Exception as e:
        print(f"Error descargando {filename}: {e}")
        return "failed", filename


def fetch_total_granules_count_from_cmr(short_name: str, version: str, **params):
    """Fetches the total number of granules for a given collection and filters from the CMR API"""
    response, _ = query_cmr_granules(short_name, version, page_size=1, **params)
    data = response.json()
    return data.get("hits", 0)


def main():
    """Main function to download data from the CMR API"""
    filter_params = {}

    if FILTER_TEMPORAL:
        filter_params["temporal"] = FILTER_TEMPORAL

    if FILTER_BBOX:
        filter_params["bounding_box"] = FILTER_BBOX

    if FILTER_SEARCH:
        filter_params["producer_granule_id[]"] = FILTER_SEARCH
        filter_params["options[producer_granule_id][pattern]"] = 'true'

    if FILTER_CLOUD_COVER_MIN and FILTER_CLOUD_COVER_MAX:
        filter_params["cloud_cover"] = f"{FILTER_CLOUD_COVER_MIN},{FILTER_CLOUD_COVER_MAX}"

    total_granules = fetch_total_granules_count_from_cmr(
        SHORT_NAME, VERSION, **filter_params
    )
    print(f"Total granules: {total_granules:,}")
    if total_granules != 299:
        raise RuntimeError("El catálogo no devuelve los 299 meses esperados. Revisar antes de descargar.")
    print("Destino:", DOWNLOAD_DIR)
    print("Introduce tu cuenta Earthdata en esta terminal. La contraseña no se muestra ni se guarda en archivos.")
    auth = earthaccess.login(strategy="interactive", persist=False)
    if not auth.authenticated:
        raise RuntimeError("No se pudo autenticar la cuenta Earthdata")
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    download_data_from_cmr(SHORT_NAME, VERSION, total_granules, **filter_params)

    print("✅ All downloads complete.")


if __name__ == "__main__":
    main()
