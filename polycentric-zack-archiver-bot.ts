import * as AbstractLevel from 'abstract-level';
import * as ClassicLevel from 'classic-level';
import fetch from 'node-fetch';
import * as FS from 'fs';
import * as NodeHTMLParser from 'node-html-parser';

import * as Core from '@polycentric/polycentric-core';
import * as LevelDb from '@polycentric/polycentric-leveldb';
import Long from 'long';
import { PrivateKey } from '@polycentric/polycentric-core/dist/protocol';

function sleep(ms: number) {
    return new Promise((resolve) => {
        setTimeout(resolve, ms);
    });
}

function Base64ToUInt8Array(base64String: string): Uint8Array {
    const binaryString = atob(base64String);
    const length = binaryString.length;
    const uint8Array = new Uint8Array(length);

    for (let i = 0; i < length; i++) {
        uint8Array[i] = binaryString.charCodeAt(i);
    }

    return uint8Array;
}

function UInt8ArrayToBase64(uint8Array: Uint8Array): string {
    const binaryString = String.fromCharCode.apply(null, uint8Array);
    const base64String = btoa(binaryString);

    return base64String;
}

export async function publishZackArchive(
    stateDirectoryPath: string,
    // profilePicturePath: string,
    username: string,
    description: string,
    zackArchiveContent: any,

    privateKeyId: Long,
    privateKeyData: String,
    processId: String,
) {
    // const persistenceDriver = LevelDb.createPersistenceDriverLevelDB(stateDirectoryPath + "/LevelDB");
    const persistenceDriver = Core.PersistenceDriver.createPersistenceDriverMemory();
    const metaStore = await Core.MetaStore.createMetaStore(persistenceDriver);
    
    const privateKey = Core.Models.PrivateKey.fromProto(
        Core.Protocol.PrivateKey.fromJSON({
            keyType: privateKeyId,
            key: privateKeyData
        })
    )

    const processHandle = await Core.ProcessHandle.createProcessHandleFromKey(metaStore, privateKey);
    // processHandle.processSecret
    {
        const servers = ["https://srv1-prod.polycentric.io"] // process.env.POLYCENTRIC_SERVERS?.split(',') ?? [];

        processHandle.setUsername(username);
        processHandle.setDescription(description);
        // processHandle.setAvatar(imagePointer);
        for (const server of servers) {
            processHandle.addServer(server);
        }
    }


    // console.log(processHandle.process())
    // console.log(processHandle.store())

    // let zackArchiveContent2 = JSON.parse(JSON.stringify(zackArchiveContent))
    // console.log("3", zackArchiveContent2)

    let zackArchiveContentBinary = Base64ToUInt8Array(zackArchiveContent)

    let published_data = await processHandle.publish(
        Core.Models.ContentType.ContentTypeZackArchive, zackArchiveContentBinary, undefined, undefined, []
    )    

    return published_data
}
