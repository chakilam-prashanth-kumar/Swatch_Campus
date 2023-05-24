#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
© Copyright 2015-2016, 3D Robotics.
mission_basic.py: Example demonstrating basic mission operations including creating, clearing and monitoring missions.

Full documentation is provided at https://dronekit-python.readthedocs.io/en/latest/examples/mission_basic.html
"""
from __future__ import print_function
import argparse

import json
from decimal import Decimal
import signal
from dronekit import connect, VehicleMode, LocationGlobalRelative, LocationGlobal, Command
import time
import math
from pymavlink import mavutil
from time import localtime
import logging
from goprocam import GoProCamera, constants
import pymavlink
import logging
import os
import tempfile
import shutil

parser = argparse.ArgumentParser(
    description='Demonstrates basic mission operations.')
parser.add_argument('--connect',
                    help="vehicle connection target string. If not specified, SITL automatically started and used.")
args = parser.parse_args()

connection_string = args.connect
sitl = None

shootinprog = False


class Timeout():
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()


class GeoTagger(object):
    def __init__(self, vehicle=None):
        self.vehicle = vehicle
        FORMAT = '%(asctime)s, %(message)s'
        DATEFORMAT = "%d-%m-%Y, %H:%M:%S"
        logging.basicConfig(format=FORMAT, datefmt=DATEFORMAT,
                            filename="camera_log.csv", filemode='w', level=logging.INFO)
        logging.info(
            "picture number, waypoint, gimbal pitch, gimbal yaw, gimbal roll, att pitch, att yaw, att roll, latitude, longitude, altitude")

    def log_vehicle_state(self, num_picture):
        if self.vehicle:
            log_msg = ",".join(map(str, [num_picture, self.vehicle.commands.next,
                                         self.vehicle.gimbal.pitch,
                                         self.vehicle.gimbal.yaw,
                                         self.vehicle.gimbal.roll,
                                         self.vehicle.attitude.pitch,
                                         self.vehicle.attitude.yaw,
                                         self.vehicle.attitude.roll,
                                         self.vehicle.location.global_frame.lat,
                                         self.vehicle.location.global_frame.lon,
                                         self.vehicle.location.global_frame.alt
                                         ]))
            pic = ""
            pic += str(self.vehicle.location.global_frame.lat)+"_"+str(
                self.vehicle.location.global_frame.lon)+"_"+str(self.vehicle.location.global_frame.alt)
            pic += "_"+str(num_picture)+".jpg"
            shootinprog = True
            gpCam = GoProCamera.GoPro(
                ip_address=GoProCamera.GoPro.getWebcamIP("usb0"))
            gpCam.downloadLastMedia(gpCam.take_photo(), custom_filename=pic)
            # gpCam.take_photo()
            shootinprog = False
        else:
            log_msg = str(num_picture)
        logging.info(log_msg)
        pass


class Camera(object):
    def __init__(self, wifi_password="goprohero3", geotag=True, myvehicle=None):
        self.wifipassword = wifi_password
        self.num_picture = 0
        self.geotagger = None
        if geotag:
            self.geotagger = GeoTagger(vehicle=myvehicle)

    def sync_time(self):
        lt = localtime()
        goprotime = "%{:02x}%{:02x}%{:02x}%{:02x}%{:02x}%{:02x}".format(lt.tm_year-2000,
                                                                        lt.tm_mon,
                                                                        lt.tm_mday,
                                                                        lt.tm_hour,
                                                                        lt.tm_min,
                                                                        lt.tm_sec)

    def shutter(self):
        self.num_picture += 1
        if self.geotagger:
            self.geotagger.log_vehicle_state(self.num_picture)


# Connect to the Vehicle
print('Connecting to vehicle on: %s' % connection_string)

logging.basicConfig(filename='example.log',
                    encoding='utf-8', level=logging.DEBUG)

vehicle = connect(connection_string, wait_ready=True)

camera = Camera(wifi_password="goprohero3", geotag=True, myvehicle=vehicle)

x = 0


@vehicle.on_message(['WAYPOINT_CURRENT', 'MISSION_CURRENT'])
def listener(self, name, m):
    global x
    logging.warning('MISSION_ITEM_INT')
    logging.debug(m.seq)
    if m.seq > x:
        camera.shutter()
        x += 1
    logging.warning('MISSION_ITEM_INT')
    """
@vehicle.on_message('MISSION_ITEM_INT_DATA')
def listener(self, name, m):
    logging.warning('MISSION_ITEM_INT_DATA')
    logging.debug(m.seq)
    logging.warning('MISSION_ITEM_INT_DATA')
    """


@vehicle.on_message('SYS_STATUS')
def listener(self, name, m):
    logging.warning('SYS_STATUS')
    logging.debug(m.battery_remaining)
    logging.warning('SYS_STATUS')


@vehicle.on_message('SYSTEM_TIME')
def listener(self, name, m):
    logging.warning('SYSTEM_TIME')
    logging.debug(m.time_unix_usec)
    logging.warning('SYSTEM_TIME')


while True:
    time.sleep(1)
