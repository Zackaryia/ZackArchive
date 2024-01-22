# Reimpl of https://gitlab.futo.org/videostreaming/grayjay/-/blob/master/app/src/main/java/com/futo/platformplayer/polycentric/PolycentricCache.kt

import random, base64, os, requests
from time import sleep

from javascript import require

import protocol_pb2 as proto
import torrent


# I am not a fan of protobuf :P

class ZackArchive:
    def __init__(
        retrieval_epoch_millis,
        plugin_signature,
        plugin_version,
        plugin_author,
        zack_archive_version,
        platform,
        content_type,
        author_id,
        content_id,
        data_type,
        data_name,
        file_length,
        file_name,
        btv2_infohash,
        sha256_merkle_hash,
        sha256_hash,
        blake3_hash, torrent_pieces
    ):

        self.retrieval_epoch_millis = retrieval_epoch_millis
        self.plugin_signature = plugin_signature
        self.plugin_version = plugin_version
        self.plugin_author = plugin_author

        self.zack_archive_version = zack_archive_version

        self.platform = platform
        self.content_type = content_type
        self.author_id = author_id
        self.content_id = content_id
        self.data_type = data_type
        self.data_name = data_name

        self.file_length = file_length
        self.file_name = file_name
        self.btv2_infohash = btv2_infohash
        self.sha256_merkle_hash = sha256_merkle_hash
        self.sha256_hash = sha256_hash
        self.blake3_hash = blake3_hash

        self.torrent_pieces = torrent_pieces


def create_zack_archive_proto(
    grayjay_plugin_signature,
    grayjay_plugin_version,
    grayjay_plugin_author,
    
    zack_archive_version,

    content_type,
    source_type,

    grayjay_content_data, 
    content_file_path,
    content_file_data_source,
    content_retrieval_time,
    torrent_meta: torrent.Torrent, 
    # infohash, 
    hashes
):
    zack_archive_proto = proto.ZackArchive()

    zack_archive_proto.retrieval_epoch_millis = round(content_retrieval_time*1000)
    
    zack_archive_proto.plugin_signature = grayjay_plugin_signature
    zack_archive_proto.plugin_version = grayjay_plugin_version
    zack_archive_proto.plugin_author = grayjay_plugin_author
    
    zack_archive_proto.zack_archive_version = zack_archive_version
    
    zack_archive_proto.platform = grayjay_content_data["id"]["platform"]
    zack_archive_proto.content_type = content_type
    zack_archive_proto.author_id = grayjay_content_data["author"]["id"]["value"]
    zack_archive_proto.content_id = grayjay_content_data["id"]["value"]

    if "Video" in content_file_data_source["plugin_type"]:
        data_type = "Video"

        if grayjay_content_data["id"]["platform"] == "YouTube":
            data_source_id = 1

            # data_source = 
    if "Audio" in content_file_data_source["plugin_type"]:
        data_type = "Audio"
        
        if grayjay_content_data["id"]["platform"] == "YouTube":
            data_source_id = 2

    zack_archive_proto.data_type = data_type
    zack_archive_proto.data_source_type = data_source_id
    zack_archive_proto.data_source = b"TODO" # Convert content_file_data_source to a proto bytes
    
    # http://bittorrent.org/beps/bep_0052.html
    torrent = torrent_meta.metafile("None")

    assert len(torrent[b"info"][b"file tree"]) == 1
    # assert list(torrent[b"info"][b"file tree"].values())[0][b""][b"length"] == torrent[b"info"][b"length"]
    assert list(torrent[b"info"][b"file tree"].keys())[0] == bytes(torrent[b"info"][b"name"], "utf-8")
    assert torrent[b"info"][b"meta version"] == 2
    if list(torrent[b"info"][b"file tree"].values())[0][b""][b"length"] > torrent[b"info"][b"piece length"]:
        assert len(torrent[b"piece layers"]) == 1
        assert list(torrent[b"piece layers"].keys())[0] == list(torrent[b"info"][b"file tree"].values())[0][b""][b"pieces root"]
        piece_layers = list(torrent[b"piece layers"].values())[0]
    else:
        assert len(torrent[b"piece layers"]) == 0
        piece_layers = bytearray()

    zack_archive_proto.file_length = list(torrent[b"info"][b"file tree"].values())[0][b""][b"length"]
    zack_archive_proto.file_name = list(torrent[b"info"][b"file tree"].keys())[0]
    zack_archive_proto.btv2_infohash = torrent_meta.info_hash_v2()
    zack_archive_proto.sha256_merkle_hash = list(torrent[b"info"][b"file tree"].values())[0][b""][b"pieces root"]
    zack_archive_proto.sha256_hash = hashes["sha256"]
    zack_archive_proto.blake3_hash = hashes["blake3"]

    zack_archive_proto.torrent_piece_layers = bytes(piece_layers)
    
    return zack_archive_proto

def publish_zack_archive(
    config,
    zack_archive_content_proto,
):
    zack_archive_content_b64 = str(base64.b64encode(zack_archive_content_proto.SerializeToString()), encoding="utf-8")
    polycentric_bot = require(config.polycentric.bot.js_path)
    # polycentric_bot.timeout = 100000
    print(
        "Published Zack Archive!",
        polycentric_bot.publishZackArchive(
            os.path.join(config.folder.data, "poly-bot"),
            config.polycentric.bot.username,
            config.polycentric.bot.description,
            zack_archive_content_b64,

            config.polycentric.bot.private_key_id,
            config.polycentric.bot.private_key_data,
            # config.polycentric.bot.process_id,
        )
    )


# def download_zack_archive(
#     config,
#     url
# ):
#     requests.get(config.polycentric.bot.servers[0], {
#         "system": config.polycentric.
#     })
    

