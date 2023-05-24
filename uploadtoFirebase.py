import pyrebase
import os
from glob import glob
from PIL import Image
import websockets
import io
import asyncio
import json


def find(direct):
    l1 = []
    filename_list = glob(os.path.join(direct, "*.jpg"))
    for filename in filename_list:
        length = len(direct)+1
        l1.append(filename[length:])
    return l1


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
            if (message['message'] == "SENDIMAGES"):
                print("SENDING Images to TDC....")
                firebase_storage = pyrebase.initialize_app(config)
                storage = firebase_storage.storage()
                l2 = find('C:/Users/dsarv/OneDrive/Desktop/Images')
                print(l2)
                for i in range(len(l2)):
                    print(l2[i])
                    storage.child('Images/'+l2[i]).put(
                        'C:/Users/dsarv/OneDrive/Desktop/Images/'+l2[i])
                    print(l2[i])
                await websocket.send('{"action":"sendmessage" , "message":"UPLOADEDTOCLOUD"}')
                exit(0)

# ---INTERNET CHECK CODE---

asyncio.get_event_loop().run_until_complete(hello())
