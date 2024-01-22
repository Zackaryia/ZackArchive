# Zack Archive
### What Problem does ZA Solve?
Zack Archive is a tool to backup the internet. The main issue with yt-dlp is that if you download a YouTube video, no one else can download it from you. Torrents have solved this issue by providing an easy and convinent method to share files however there still remains the issues of searchability, which is self-explanitory, and authenticity. There is no verifying that a torrent is really a mirror of what the live YouTube video shows or showed. 

### Why PolyCentric?
PolyCentric, created by FUTO, is a solution to this problem. It provides a microblogging platform to share small snippits of data and also has a verification system to allow you to vet any sources of information. And as a bonus you can use their API to search for certain events that match your criteria. 

### Why GrayJay Plugins?
Grayjay Plugins are used as a backend to download content (Currently just from YouTube). It is used because of its relation to PolyCentric, both being developed by FUTO, and its reduction in varaibles. We want to prevent fragmentation of seeders seeding multiple torrents, so using GrayJay to consistently pull youtube videos bit-for-bit the same will allow for less fragmented torrents.

### How does it come together?
To archive a video, Zack Archive
1. Updates the GrayJay plugins
2. Runs the plugin to pull the content details
3. Extracts Video and Audio sources from the content.

Then for each source it
1. Downloads the actual source file
2. Creates a torrent for the source
3. Publishes the archive to PolyCentric
4. Seeds the content on qBittorrent to allow other users to download the videos


## How do I use this tool?
First run ./install.sh to get all related files needed
Second fill out the settings.json.example and rename it to `settings.json`
Then run the needed command below

To archive a video + host it on qBittorrent run `python3 python/main.py archive "YOUTUBE VIDEO TO ARCHIVE" --settings /absolute/path/to/settings.json`

To download a video run `python3 python/main.py pull "YOUTUBE VIDEO TO DOWNLOAD" --settings /absolute/path/to/settings.json`