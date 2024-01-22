# Git clone polycentric
git clone https://github.com/Zackaryia/PolyCentric

./polycentric-zack-archiver.sh

# Protoc
protoc polycentric/proto/protocol.proto --python_out=python
mv python/polycentric/proto/protocol_pb2.py python/
rm -rf python/polycentric/

