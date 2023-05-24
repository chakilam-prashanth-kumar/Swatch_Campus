import pyrebase
import os
from glob import glob
from PIL import Image
import websockets
import io
import asyncio
import json


config = {
    "apiKey": "AIzaSyCNIl_Uo9PxNpZHWKrefMoq1Y5hJmEqMag",
    "authDomain": "swach-119fb.firebaseapp.com",
    "projectId": "swach-119fb",
    "storageBucket": "swach-119fb.appspot.com",
    "serviceAccount": "serviceAccountKey.json",
    "databaseURL": 'gs://swach-119fb.appspot.com'
}


async def hello():
    async with websockets.connect('wss://h6zxetfwdd.execute-api.ap-southeast-1.amazonaws.com/production') as websocket:
        while True:
            message = await websocket.recv()
            message = json.loads(message)
            if (message['message'] == "UPLOADEDTOCLOUD"):
                print("Loading Images from cloud")
                firebase_storage = pyrebase.initialize_app(config)
                storage = firebase_storage.storage()
                all_files = storage.list_files()
                for file in all_files:
                    print(file.name)
                    file.download_to_filename("Images/"+file.name)
                await websocket.send('{"action":"sendmessage" , "message":"DETECTING"}')
                break

asyncio.get_event_loop().run_until_complete(hello())
