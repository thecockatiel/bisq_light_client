import os
import io
from urllib.parse import urlparse
from tqdm import tqdm
import aiohttp
from bisq.common.config.config import CONFIG

HTTP_HEADERS = {'User-Agent': 'Electrum-Bisq/1.0'}

async def download_file(url: str, skip_if_exists=True):
    download_dir = CONFIG.app_data_dir.joinpath('downloads')
    download_dir.mkdir(parents=True, exist_ok=True)
    filename: str = os.path.basename(urlparse(url).path)
    download_path = download_dir.joinpath(filename)

    chunk_size = io.DEFAULT_BUFFER_SIZE
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                total_size = int(response.headers.get("content-length", 0))
                # if the file already exists and has the same size, skip the download
                if skip_if_exists and download_path.is_file():
                    if download_path.stat().st_size == total_size:
                        return download_path
                    else:
                        download_path.unlink(missing_ok=True)
                # download the file with progress bar
                with tqdm(total=total_size, unit="B", unit_scale=True, desc=filename) as progress_bar:
                    response.raise_for_status()
                    with download_path.open('wb') as f:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            if chunk:  # filter out keep-alive new chunks
                                progress_bar.update(len(chunk))
                                f.write(chunk)
                                f.flush()
    except Exception as e:
        download_path.unlink(missing_ok=True)
        raise e
    return download_path
