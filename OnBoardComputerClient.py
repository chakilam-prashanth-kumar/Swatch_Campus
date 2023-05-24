import asyncio
import websockets
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
import ast


async def test():
    async with websockets.connect('wss://h6zxetfwdd.execute-api.ap-southeast-1.amazonaws.com/production') as websocket:
        await websocket.send('{"action":"sendmessage","message":"Waiting for Json"}')
        response = await websocket.recv()
        await websocket.send('{"action":"sendmessage","message":"Received Successfully"}')
        flag = 1
        return response, flag
drone_json, flag = (asyncio.get_event_loop().run_until_complete(test()))
drone_json = drone_json[7:]
print(drone_json)
drone_json = ast.literal_eval(drone_json)
drone_json = drone_json['json']

#!/usr/bin/env python
# -*- coding: utf-8 -*-

while (flag == 0):
    pass


# Set up option parsing to get connection string
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
            #gpCam.downloadLastMedia(gpCam.take_photo(), custom_filename=pic)
            gpCam.take_photo()
            shootinprog = False
        else:
            log_msg = str(num_picture)
        logging.info(log_msg)
        pass


# Connect to the Vehicle
print('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True)

camera = Camera(wifi_password="goprohero3", geotag=True, myvehicle=vehicle)


def get_location_metres(original_location, dNorth, dEast):
    """
    Returns a LocationGlobal object containing the latitude/longitude `dNorth` and `dEast` metres from the 
    specified `original_location`. The returned Location has the same `alt` value
    as `original_location`.

    The function is useful when you want to move the vehicle around specifying locations relative to 
    the current vehicle position.
    The algorithm is relatively accurate over small distances (10m within 1km) except close to the poles.
    For more information see:
    http://gis.stackexchange.com/questions/2951/algorithm-for-offsetting-a-latitude-longitude-by-some-amount-of-meters
    """
    earth_radius = 6378137.0  # Radius of "spherical" earth
    # Coordinate offsets in radians
    dLat = dNorth/earth_radius
    dLon = dEast/(earth_radius*math.cos(math.pi*original_location.lat/180))

    # New position in decimal degrees
    newlat = original_location.lat + (dLat * 180/math.pi)
    newlon = original_location.lon + (dLon * 180/math.pi)
    return LocationGlobal(newlat, newlon, original_location.alt)


def get_distance_metres(aLocation1, aLocation2):
    """
    Returns the ground distance in metres between two LocationGlobal objects.

    This method is an approximation, and will not be accurate over large distances and close to the 
    earth's poles. It comes from the ArduPilot test code: 
    https://github.com/diydrones/ardupilot/blob/master/Tools/autotest/common.py
    """
    dlat = aLocation2.lat - aLocation1.lat
    dlong = aLocation2.lon - aLocation1.lon
    return math.sqrt((dlat*dlat) + (dlong*dlong)) * 1.113195e5


def distance_to_current_waypoint():
    """
    Gets distance in metres to the current waypoint. 
    It returns None for the first waypoint (Home location).
    """
    nextwaypoint = vehicle.commands.next
    if nextwaypoint == 0:
        return None
    # commands are zero indexed
    missionitem = vehicle.commands[nextwaypoint-1]
    lat = missionitem.x
    lon = missionitem.y
    alt = missionitem.z
    targetWaypointLocation = LocationGlobalRelative(lat, lon, alt)
    distancetopoint = get_distance_metres(
        vehicle.location.global_frame, targetWaypointLocation)
    return distancetopoint


def download_mission():
    """
    Download the current mission from the vehicle.
    """
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()  # wait until download is complete.


def adds_square_mission(aLocation, aSize):
    """
    Adds a takeoff command and four waypoint commands to the current mission. 
    The waypoints are positioned to form a square of side length 2*aSize around the specified LocationGlobal (aLocation).

    The function assumes vehicle.commands matches the vehicle mission state 
    (you must have called download at least once in the session and after clearing the mission)
    """

    cmds = vehicle.commands

    print(" Clear any existing commands")
    cmds.clear()

    print(" Define/add new commands.")
    # Add new commands. The meaning/order of the parameters is documented in the Command class.

    # Add MAV_CMD_NAV_TAKEOFF command. This is ignored if the vehicle is already in the air.
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_TAKEOFF, 0, 0, 0, 0, 0, 0, 0, 0, 8))

    # Define the four MAV_CMD_NAV_WAYPOINT locations and add the commands
    point1 = get_location_metres(aLocation, aSize, -aSize)
    point2 = get_location_metres(aLocation, aSize, aSize)
    point3 = get_location_metres(aLocation, -aSize, aSize)
    point4 = get_location_metres(aLocation, -aSize, -aSize)

    # Python program to read
    data = drone_json
    for i in data:
        cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                         mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, float(i["hold(s)"]), 0, 0, 0, float(i["latitude"]), float(i["longitude"]), float(i["altitude(m)"])))

    # add dummy waypoint "5" at point 4 (lets us know when have reached destination
    cmds.add(Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                     mavutil.mavlink.MAV_CMD_NAV_WAYPOINT, 0, 0, 0, 0, 0, 0, point4.lat, point4.lon, 6))

    print(" Upload new commands to vehicle")
    cmds.upload()


def arm_and_takeoff(aTargetAltitude):
    """
    Arms vehicle and fly to aTargetAltitude.
    """

    print("Basic pre-arm checks")
    # Don't let the user try to arm until autopilot is ready
    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")
    # Copter should arm in GUIDED mode
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude)  # Take off to target altitude

    # Wait until the vehicle reaches a safe height before processing the goto (otherwise the command
    #  after Vehicle.simple_takeoff will execute immediately).
    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        # Trigger just below target alt.
        if vehicle.location.global_relative_frame.alt >= aTargetAltitude*0.95:
            print("Reached target altitude")
            break
        time.sleep(1)


print('Create a new mission (for current location)')
adds_square_mission(vehicle.location.global_frame, 0)

# From Copter 3.3 you will be able to take off using a mission item. Plane must take off using a mission item (currently).
arm_and_takeoff(15)

print("Starting mission")
# Reset mission set to first (0) waypoint
vehicle.commands.next = 0

# Set mode to AUTO to start mission
vehicle.mode = VehicleMode("AUTO")

# Monitor mission.
# Demonstrates getting and setting the command number
# Uses distance_to_current_waypoint(), a convenience function for finding the
#   distance to the next waypoint.
while True:
    nextwaypoint = vehicle.commands.next
    dist = distance_to_current_waypoint()
    print('Distance to waypoint (%s): %s' % (nextwaypoint, dist))
    if True:  # Just below target, in case of undershoot.
        try:
            if not shootinprog:
                camera.shutter()
        except:
            pass
    # if nextwaypoint==3: #Skip to next waypoint
    #     print('Skipping to Waypoint 5 when reach waypoint 3')
    #     vehicle.commands.next = 5
    # Dummy waypoint - as soon as we reach waypoint 4 this is true and we exit.
    if nextwaypoint == len(drone_json)-1:
        print("Exit 'standard' mission when start heading to final waypoint (5)")
        break
    time.sleep(1)

print('Return to launch')
vehicle.mode = VehicleMode("RTL")

# Close vehicle object before exiting script
print("Close vehicle object")
vehicle.close()

# Shut down simulator if it was started.
if sitl is not None:
    sitl.stop()
