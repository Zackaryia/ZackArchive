
# Reimpl of https://gitlab.futo.org/videostreaming/grayjay/-/blob/master/app/src/main/java/com/futo/platformplayer/downloads/VideoDownload.kt

import os, math, requests, shutil
from pathlib import Path
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

def download_chunk(url, start_byte, end_byte, filename):
	print(f"Downloading Chunk {start_byte}-{end_byte} in {filename}")
	headers = {'Range': f'bytes={start_byte}-{end_byte}'}
	response = requests.get(url, headers=headers, stream=True)
	with open(filename, 'wb') as file:
		file.write(response.content)
	print(f"Downloaded Chunk {start_byte}-{end_byte} in {filename}")


def download_file(config, url, destination_directory, parallel=False, filename=None):
	if filename == None:
		filename = url.split("/")[-1].split("?")[0]
	
	file_path = os.path.join(destination_directory, filename)

	Path(destination_directory).mkdir(parents=True, exist_ok=True)

	if parallel == False:
		response = requests.get(url)

		with open(file_path, 'wb') as file:
			file.write(response.content)

		print(f"File downloaded and saved to {file_path}")

		return response.content


	Path(os.path.join(config.folder.tmp, filename)).mkdir(parents=True, exist_ok=True)

	response = requests.head(url, allow_redirects=True)
	total_size = int(response.headers['content-length'])

	chunk_size = config.download.chunk_size  # 512KiB chunks
	num_chunks = math.ceil(total_size / chunk_size)

	with ThreadPoolExecutor(max_workers=config.download.range_threads) as executor:
		futures = []
		for i in range(num_chunks):
			start_byte = i * chunk_size
			end_byte = min((i + 1) * chunk_size - 1, total_size - 1)
			futures.append(
				executor.submit(download_chunk, url, start_byte, end_byte, os.path.join(config.folder.tmp, filename, f"chunk_{start_byte}-{end_byte}"))
			)

		# Wait for all futures to complete
		for future in futures:
			future.result()


	chunks = [f for f in os.listdir(os.path.join(config.folder.tmp, filename)) if os.path.isfile(os.path.join(config.folder.tmp, filename, f))]
	chunks.sort()
	
	Path(destination_directory).mkdir(parents=True, exist_ok=True)

	with open(file_path, 'wb') as output:
		for chunk in chunks:
			with open(os.path.join(config.folder.tmp, filename, chunk), 'rb') as file:
				content = file.read()
				output.write(content)

	print(f"File downloaded and saved to {file_path}")

	shutil.rmtree(config.folder.tmp)

