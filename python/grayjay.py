import os, requests, json, urllib.parse, time, urllib3, http, datetime
from enum import Enum

import STPyV8

import util
import download

# region GrayJay Compatability Imports

# TODO there are other packages that need to be implimented
# plus this impl dosnt limit things like what websites the
# plugin has access to which is probably a good idea to do
# to keep inline with the actual impl

class Batch(STPyV8.JSClass):
	def __init__(self):
		self.tasks = []

	def GET(self, url, headers, useAuth=False):
		body = None
		self.tasks.append(("GET", url, headers, body, useAuth))
		return self
	
	def POST(self, url, body, headers, useAuth=False):
		self.tasks.append(("POST", url, headers, body, useAuth))
		return self
	
	def execute(self):
		resps = []

		http = Http()

		for task in self.tasks:
			resps.append(http.request(task[0], task[1], task[2], body = task[3], useAuth=task[4]))

		return resps

class Http(STPyV8.JSClass):
	def request(self, method, url, headers, body=None, useAuth=False):
		# TODO useAuth is currently ignored
		
		new_headers = {}
		for key in headers.keys():
			new_headers[key] = headers.__getitem__(key)
		headers = new_headers

		if body != None:
			resp = requests.request(method, url, data=body, headers=headers)
		else:
			resp = requests.request(method, url, headers=headers)

		if util.DEBUG == 1:
			with open(f"debug/{time.time()}-{resp.url.replace('/', '_')})json", "w") as file:
				json.dump(resp.__dict__, file, cls=BytesEncoder, indent="\t")

		resp = response(resp.url, resp.status_code, resp.content.decode('utf-8'), resp.headers)

		if util.DEBUG == 1:
			with open(f"debug/{time.time()}-reformatted-{resp.url.replace('/', '_')}.json", "w") as file:
				json.dump(resp.__dict__, file, cls=BytesEncoder)

		return resp

	def GET(self, url, headers, UseAuth=False):
		return self.request("GET", url, headers, useAuth=UseAuth)

	def POST(self, url, body, headers, UseAuth=False):
		return self.request("POST", url, headers, body=body, useAuth=UseAuth)

	def batch(self):
		return Batch()

class response(STPyV8.JSClass):
	def __init__(self, url: str, code: int, body: str, headers: dict):
		self.url = url
		self.code = code
		self.body = body
		self.headers = headers

	def __getattr__(self, name):
		if name == "isOk":
			return self.code >= 200 and self.code < 300
# endregion GrayJay Compatability Imports


def download_plugins(config: util.Config):
	download_directory = os.path.join(config.folder.data, "grayjay_plugin")
	download.download_file(config, config.plugin.source_js, download_directory)

	for plugin_config_url in config.plugin.config_urls:
		# Download Plugin Config JSON
		json_data = json.loads(download.download_file(config, plugin_config_url, download_directory))
		# Download Plugin Script JS
		download.download_file(config, urllib.parse.urljoin(plugin_config_url, json_data['scriptUrl']), download_directory)

def execute_plugin_get_content_details(config, plugin_name, url):
	return execute_plugin(config, f"source.getContentDetails(\"{url}\"", plugin_name)

def execute_plugin(config, command, plugin_name="Youtube", console_log_to_print=False):
	plugin_folder = os.path.join(config.folder.data, "grayjay_plugin")

	with open(os.path.join(plugin_folder, f"{plugin_name}Script.js"), 'r') as file:
		plugin_js_data = file.read()
	with open(os.path.join(plugin_folder, f"source.js"), 'r') as file:
		source_js_data = file.read()

	with STPyV8.JSContext({
		# http is a doubious reimpl of http https://gitlab.futo.org/videostreaming/grayjay/-/blob/master/app/src/main/java/com/futo/platformplayer/engine/packages/PackageHttp.kt
		"http": Http(), 
		# response is a doubious reimpl of BridgeHttpResponse https://gitlab.futo.org/videostreaming/grayjay/-/blob/master/app/src/main/java/com/futo/platformplayer/engine/packages/PackageHttp.kt
		"response": response, 

		# Doubious reimpl of https://gitlab.futo.org/videostreaming/grayjay/-/blob/master/app/src/main/java/com/futo/platformplayer/engine/packages/PackageBridge.kt
		"bridge": {"log": lambda message: print(f"JS Bridge: {message}") if console_log_to_print else None, "isLoggedIn": lambda: False}, 
	}) as ctxt:
		if console_log_to_print:
			# Allows piping of js prints to python
			ctxt.eval("var console = {}; console.log = function(x){print(x)} ")
	
		print(ctxt.eval(source_js_data))
		print(ctxt.eval(plugin_js_data))

		data = json.loads(ctxt.eval(f"JSON.stringify({command}))"))

	return data



# TODO Maybe add a parser for this file https://gitlab.futo.org/videostreaming/grayjay/-/raw/master/app/src/main/java/com/futo/platformplayer/api/media/IPlatformClient.kt 
# So that we can automatically create a class PlatformClient that has all the functions to interact with the plugin. 