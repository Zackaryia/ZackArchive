import os, pathlib, json, requests, math, time
from base64 import b64decode, b64encode, urlsafe_b64encode
from hashlib import sha256

from blake3 import blake3
import plyvel
import click

import grayjay
import download
import torrent
import polycentric
import util
import protocol_pb2 as proto

from util import style
from tqdm import tqdm

@click.group()
def cli():
    pass

@click.command()
@click.argument('url')
# @click.option('--', help='content to archive')
@click.option('--settings', help='location of your settings.json file')
def archive(url, settings):
    with open(settings, 'r') as settings_file:
        config = util.Config(json.load(settings_file))

    grayjay.download_plugins(config)

    archive_yt_video(config, content_identifier=url)

@click.command()
@click.argument('url')
# @click.option('--', help='content to archive')
@click.option('--settings', help='location of your settings.json file')
def pull(url, settings):
    with open(settings, 'r') as settings_file:
        config = util.Config(json.load(settings_file))

    valid_archives = []
    
    print("Pulling data from PolyCentric")

    for trusted_archiver in config.polycentric.trusted_archivers:
        # czbkEGCCDDPqChea1NeGhgoGXLMHYnc5h7RogdMfndo=
        public_key = proto.PublicKey()
        
        public_key.key_type = 1
        public_key.key = b64decode(trusted_archiver)

        # print("URLSAFE", urlsafe_b64encode(public_key.SerializeToString()))
        # print(trusted_archiver)

        ranges_for_system_bytes = requests.get(f"{config.polycentric.servers[0]}/ranges", {
            "system": urlsafe_b64encode(public_key.SerializeToString()),
            # "ranges": urlsafe_b64encode(ranges_systems.SerializeToString()),
            # "limit": 1000
        })

        # print(ranges_for_system_bytes.__dict__)

        ranges_for_system = proto.RangesForSystem()
        ranges_for_system.ParseFromString(ranges_for_system_bytes.content)

        # print(ranges_for_system)

        # ranges_for_system = proto.Events()

        # print(urlsafe_b64encode(ranges_for_system_bytes.content).replace(b'=', b''))
        events_bytes = requests.get(f"{config.polycentric.servers[0]}/events", {
            "system": urlsafe_b64encode(public_key.SerializeToString()),
            "ranges": urlsafe_b64encode(ranges_for_system_bytes.content).replace(b'=', b'') #urlsafe_b64encode(ranges_for_system.SerializeToString()),
            # "limit": 1000
        })

        # print(events_bytes.url)
        # print(events_bytes.content)
        # print(events_ranges.content))
        signed_events = proto.Events()
        signed_events.ParseFromString(events_bytes.content)

        for signed_event in signed_events.events:
            # print("Sigend", signed_event)
            unsigned_event = proto.Event()
            unsigned_event.ParseFromString(signed_event.event)
            
            # print("USE", unsigned_event)
            # print("USE_KEY", b64encode(unsigned_event.process.process))
            
            if unsigned_event.content != b'':
                zack_archive = proto.ZackArchive()
                zack_archive.ParseFromString(unsigned_event.content)

                valid_archives.append(zack_archive)

    def display_valid_archive(zack_archive):
        plugin_info = {
            "Downloadable File Info": [
                ("File Name", zack_archive.file_name),
                ("File Length", f"{ round(zack_archive.file_length / 1024) } KB"),
                ("Data Type", zack_archive.data_type),
                ("Blake3 Hash", urlsafe_b64encode(zack_archive.blake3_hash).decode('utf-8')),
                ("Sha256 Hash", urlsafe_b64encode(zack_archive.sha256_hash).decode('utf-8')),
                ("Sha256 Merkle Hash", urlsafe_b64encode(zack_archive.sha256_merkle_hash).decode('utf-8')),
                ("Bit Torrent V2 Info Hash", urlsafe_b64encode(zack_archive.btv2_infohash).decode('utf-8')),
            ],

            "Content Info": [
                ("Platform", zack_archive.platform), 
                ("Content Type", zack_archive.content_type), 
                ("Content Author ID", zack_archive.author_id),
                ("Content ID", zack_archive.content_id),
            ],

            "Plugin Info": [
                ("Author", zack_archive.plugin_author),
                ("Version", zack_archive.plugin_version)
            ],
        }

        for k, v in plugin_info.items():
            print(f"{style.RED}{k}{style.RESET}")
            for k, v in v:
                print(f"{style.UNDERLINE}{k}:{style.RESET} {v}")

    if len(valid_archives) == 0:
        print("No valid archives found :(")
        return
    elif len(valid_archives) == 1:
        print("One valid archive found")
    else:
        print("Multiple valid archives found")

    for number, archive in enumerate(valid_archives):
        print(f"\n{style.MAGENTA}Archive #{number + 1}{style.RESET}")
        display_valid_archive(archive)

    selected_files = input(f"{style.GREEN}Enter the number(s) associated with the archive(s) you would like to download in a comma seperated list or \"None\". {style.RESET} ")

    if selected_files == "None":
        return

    selected_files = [valid_archives[int(x.strip())-1] for x in selected_files.split(',')]

    print(f"{style.RED}Submitting info hash(es) {['magnet:?xt=urn:btmh:1220'+util.bytes_to_hex(x.btv2_infohash) for x in selected_files]} to your qBitTorrent web API {style.RESET}")

    while True:
        resp = input(f"Continue? Y/N")
        if resp.lower() == "y":
            break
        elif resp.lower() == "n":
            print("Exiting program")
            exit()

    for archive in selected_files:
        torrent.download_torrent(
            config, 
            torrent_magnet=f"magnet:?xt=urn:btmh:1220{util.bytes_to_hex(archive.btv2_infohash)}", 
            storage_file_path=os.path.join(config.folder.data, "torrent_downloads")
        )

cli.add_command(archive)
cli.add_command(pull)


def archive_source(config: util.Config, grayjay_source_data, grayjay_content_data, content_type, source_type):
    print(f"{style.RED}1/4 {source_type} Archiving:{style.RESET} Downloading {source_type} Source stream")
    output_file_name = f"ZackArchive_{grayjay_content_data['id']['platform']}_{grayjay_content_data['id']['value']}_{content_type}_{grayjay_source_data['name'].split(' ')[0]}.{grayjay_source_data['container'].split('/')[1]}"

    source_file_path = os.path.join(os.path.join(config.folder.data, "archived_source", source_type), output_file_name)

    download.download_file(
        config,
        grayjay_source_data["url"], 
        os.path.join(config.folder.data, "archived_source", source_type),
        parallel=True,
        filename = output_file_name,
    )

    retrieved_time = time.time()
    print(f"{style.RED}1/4 {source_type} Archiving:{style.RESET} Downloading {source_type} Source stream {style.GREEN}DONE{style.RESET}")

    print(f"{style.RED}2/4 {source_type} Archiving:{style.RESET} Creating torrent for {source_type} stream")
    torrent_file_path = os.path.join(config.folder.data, "torrent", os.path.basename(source_file_path) + ".torrent")
    torrent_metafile = torrent.create_torrent(config, source_file_path, torrent_file_path)
    hashes = util.get_content_hashes(source_file_path)
    print(f"{style.RED}2/4 {source_type} Archiving:{style.RESET} Creating torrent for {source_type} stream {style.GREEN}DONE{style.RESET}")

    print(f"{style.RED}3/4 {source_type} Archiving:{style.RESET} Publishing archived {source_type} stream to PolyCentric")
    zack_archive_proto = polycentric.create_zack_archive_proto(
        grayjay_plugin_signature=b"test", # TODO
        grayjay_plugin_version=1, # TODO
        grayjay_plugin_author="test", # TODO

        zack_archive_version=0, # TODO

        content_type = content_type, 
        source_type = source_type,

        grayjay_content_data=grayjay_content_data,
        content_file_path=source_file_path,
        content_file_data_source=grayjay_source_data,
        content_retrieval_time=retrieved_time,
        torrent_meta=torrent_metafile,
        hashes=hashes,
    )

    polycentric.publish_zack_archive(config, zack_archive_proto)
    print(f"{style.RED}3/4 {source_type} Archiving:{style.RESET} Publishing archived {source_type} stream to PolyCentric {style.GREEN}DONE{style.RESET}")

    print(f"{style.RED}4/4 {source_type} Archiving:{style.RESET} Publishing content to qBittorrent")
    torrent.add_torrent(config, torrent_file_path, os.path.join(config.folder.data, "archived_source", source_type))
    print(f"{style.RED}4/4 {source_type} Archiving:{style.RESET} Publishing content to qBittorrent {style.GREEN}DONE{style.RESET}")



def archive_yt_video(config: util.Config, content_identifier, content_type = "Video"):
     # content_type: YouTube only has Video content, if this was archiving twitter maybe it would be microblogs or something

    print(f"{style.RED}1/3 GrayJay:{style.RESET} Downloading most recent plugin version data")
    grayjay.download_plugins(config)
    print(f"{style.RED}1/3 GrayJay:{style.RESET} Downloading most recent plugin version data {style.GREEN}DONE{style.RESET}")
    
    print(f"{style.RED}2/3 GrayJay:{style.RESET} Downloading {content_type} Metadata {content_identifier}")
    grayjay_content_data = grayjay.execute_plugin_get_content_details(config, "Youtube", content_identifier)
    print(f"{style.RED}2/3 GrayJay:{style.RESET} Downloading {content_type} Metadata {content_identifier} {style.GREEN}DONE{style.RESET}")


    with open("a.json", "w") as a:
        json.dump(grayjay_content_data, a)

    print(f"{style.RED}3/3 GrayJay:{style.RESET} Extracting Video & Audio source stream from Metadata")
    video_file_source = config.get_stream(grayjay_content_data["video"]["videoSources"])
    audio_file_source = config.get_stream(grayjay_content_data["video"]["audioSources"])

    # Sanity check incase the source is only part of the video.
    assert abs(video_file_source["duration"] - grayjay_content_data["duration"]) <= 1
    assert abs(audio_file_source["duration"] - grayjay_content_data["duration"]) <= 1
    print(f"{style.RED}3/3 GrayJay:{style.RESET} Extracting Video & Audio source stream from Metadata {style.GREEN}DONE{style.RESET}")



    print(f"Downloading Source: {'Video'}")
    archive_source(config, video_file_source, grayjay_content_data, content_type, "Video")

    print(f"Downloading Source: {'Audio'}")
    archive_source(config, audio_file_source, grayjay_content_data, content_type, "Audio")



if __name__ == "__main__":
    cli()