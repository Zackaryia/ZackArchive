import os, requests, json, urllib.parse, urllib3, datetime, http, math, time
from enum import Enum
from hashlib import sha256

from blake3 import blake3
import STPyV8

import util

DEBUG = int(os.getenv('DEBUG', 0))


class BytesEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, bytes):
			return obj.decode('utf-8')
		print(obj)
		if isinstance(obj, requests.structures.CaseInsensitiveDict):
			return obj.__dict__
		if isinstance(obj, urllib3.response.HTTPResponse):
			return obj.__dict__
		if isinstance(obj, urllib3._collections.HTTPHeaderDict):
			return obj.__dict__
		if isinstance(obj, urllib3.util.Retry):
			return obj.__dict__
		if isinstance(obj, set):
			return list(obj)
		if isinstance(obj, frozenset):
			return list(obj)
		if isinstance(obj, urllib3.response.GzipDecoder):
			return "urllib3.response.GzipDecoder"
		if isinstance(obj, http.client.HTTPResponse):
			return "http.client.HTTPResponse"
		if isinstance(obj, urllib3.HTTPSConnectionPool):
			return "urllib3.HTTPSConnectionPool"
		if isinstance(obj, requests.cookies.RequestsCookieJar):
			return obj.get_dict()
		if isinstance(obj, datetime.timedelta):
			return obj.__str__()
		if isinstance(obj, requests.models.PreparedRequest):
			return obj.__repr__()
		if isinstance(obj, requests.adapters.HTTPAdapter):
			return obj.__repr__()

		return json.JSONEncoder.default(self, obj)


class DataObject:
    pass

def dict_to_object(data_dict, obj=None):
    if obj == None:
        obj = DataObject()

    for item in data_dict.items():
        if isinstance(item[1], dict):
            item = (item[0], dict_to_object(item[1]))
        
        setattr(obj, item[0], item[1])

    return obj

class Config:
    def __init__(self, settings_json: dict):
        dict_to_object(settings_json, self)

    def torrent_peice_length(self, file_size: int):
        return 2**max(20, math.ceil(math.log2(file_size/512)))

    def get_stream(self, streams):
        if self.download.quality == "max":
            return max(streams, key=lambda f: f['bitrate'])




def get_content_hashes(path):
    with open(path, "rb") as file:
        # Todo optimize so whole file isnt in ram :P
        file_data = file.read()
        return {
            "blake3": blake3(file_data).digest(),
            "sha256": sha256(file_data).digest(),
            # "sha256_merkle":
            # Not implimented here, use the one from the torrent
            # If needed you can use the one from http://bittorrent.org/beps/bep_0052_torrent_creator.py
            # described in http://bittorrent.org/beps/bep_0052.html
        }

def bytes_to_hex(data):
	return ''.join([f'{byte:02x}' for byte in data])



# Class of different styles
class style():
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'