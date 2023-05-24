import numpy as np
import argparse
import time
import cv2
import os
from PIL import Image
import websockets
import io
import base64
import asyncio
import json
import pyrebase
import os
from glob import glob


confthres = 0.5
nmsthres = 0.1
yolo_path = "./"


def get_labels(labels_path):
    # load the COCO class labels our YOLO model was trained on
    #labelsPath = os.path.sep.join([yolo_path, "yolo_v3/coco.names"])
    lpath = os.path.sep.join([yolo_path, labels_path])
    LABELS = open(lpath).read().strip().split("\n")
    print(LABELS)
    return LABELS


def get_colors(LABELS):
    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(LABELS), 3), dtype="uint8")
    return COLORS


def get_weights(weights_path):
    # derive the paths to the YOLO weights and model configuration
    weightsPath = os.path.sep.join([yolo_path, weights_path])
    return weightsPath


def get_config(config_path):
    configPath = os.path.sep.join([yolo_path, config_path])
    return configPath


def load_model(configpath, weightspath):
    # load our YOLO object detector trained on COCO dataset (80 classes)
    print("[INFO] loading YOLO from disk...")
    net = cv2.dnn.readNetFromDarknet(configpath, weightspath)
    return net


def get_predection(image, net, LABELS, COLORS):
    if image is None:
        print('Image Empty')
        return
    (H, W) = image.shape[:2]

    # determine only the *output* layer names that we need from YOLO
    ln = net.getLayerNames()
    # print(ln)
    # print(ln[0])
    ln = [ln[i - 1] for i in net.getUnconnectedOutLayers()]

    # construct a blob from the input image and then perform a forward
    # pass of the YOLO object detector, giving us our bounding boxes and
    # associated probabilities
    blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
                                 swapRB=True, crop=False)
    net.setInput(blob)
    start = time.time()
    layerOutputs = net.forward(ln)
    print(layerOutputs)
    end = time.time()

    # show timing information on YOLO
    print("[INFO] YOLO took {:.6f} seconds".format(end - start))

    # initialize our lists of detected bounding boxes, confidences, and
    # class IDs, respectively
    boxes = []
    confidences = []
    classIDs = []

    # loop over each of the layer outputs
    for output in layerOutputs:
        # loop over each of the detections
        for detection in output:
            # extract the class ID and confidence (i.e., probability) of
            # the current object detection
            scores = detection[5:]
            # print(scores)
            classID = np.argmax(scores)
            # print(classID)
            confidence = scores[classID]

            # filter out weak predictions by ensuring the detected
            # probability is greater than the minimum probability
            if confidence > confthres:
                # scale the bounding box coordinates back relative to the
                # size of the image, keeping in mind that YOLO actually
                # returns the center (x, y)-coordinates of the bounding
                # box followed by the boxes' width and height
                box = detection[0:4] * np.array([W, H, W, H])
                (centerX, centerY, width, height) = box.astype("int")

                # use the center (x, y)-coordinates to derive the top and
                # and left corner of the bounding box
                x = int(centerX - (width / 2))
                y = int(centerY - (height / 2))

                # update our list of bounding box coordinates, confidences,
                # and class IDs
                boxes.append([x, y, int(width), int(height)])
                confidences.append(float(confidence))
                classIDs.append(classID)

    # apply non-maxima suppression to suppress weak, overlapping bounding
    # boxes
    idxs = cv2.dnn.NMSBoxes(boxes, confidences, confthres,
                            nmsthres)
    print(confidences)
    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            # draw a bounding box rectangle and label on the image
            color = [int(c) for c in COLORS[classIDs[i]]]
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
            text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
            print(boxes)
            print(classIDs)
            cv2.putText(image, text, (x, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    return image


def runModel(img):
    l = os.listdir(img)
    for i in l:
        image = cv2.imread('Images/'+i)
        if image is None:
            continue
        labelsPath = "./coco.names"
        cfgpath = "Detection_draft.cfg"
        wpath = "Detection_draft_best.weights"
        Lables = get_labels(labelsPath)
        CFG = get_config(cfgpath)
        Weights = get_weights(wpath)
        nets = load_model(CFG, Weights)
        Colors = get_colors(Lables)
        res = get_predection(image, nets, Lables, Colors)
        image = Image.fromarray(res, "RGB")
        image.save("DetectedImages/"+i)
    return None


config = {
    "apiKey": "AIzaSyCNIl_Uo9PxNpZHWKrefMoq1Y5hJmEqMag",
    "authDomain": "swach-119fb.firebaseapp.com",
    "projectId": "swach-119fb",
    "storageBucket": "swach-119fb.appspot.com",
    "serviceAccount": "serviceAccountKey.json",
    "databaseURL": 'gs://swach-119fb.appspot.com'
}

firebase_storage = pyrebase.initialize_app(config)
storage = firebase_storage.storage()
all_files = storage.list_files()
k = 0
for file in all_files:
    if k == 0:
        k += 1
        continue
    print(file.name)
    file.download_to_filename(file.name)

runModel("Images")

l = os.listdir("DetectedImages")
for i in l:
    storage.child('DetectedImages/'+i).put('DetectedImages/'+i)
    print(i)
