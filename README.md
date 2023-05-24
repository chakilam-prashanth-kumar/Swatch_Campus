# Swatch Campus -Litter Detection
## Problem Statement
We aim to provide the higher authorities responsible for sanitation and cleaning of large areas or intuitions a method for evaluation the work of their subordinates without manually inspecting the areas which might be kilometers apart.

## Solution
A surveillance drone can be deployed to perform periodic surveys of the campus to detect litter such as pet bottles,tetra packets,face masks etc., A drone will carry out a waypoint based surveillance mission in the campus, take pictures at each waypoint and feed the pictures in the DataBase after completing the mission. Then the trash detection client will fetch pictures from the DataBase and apply deep learning algorithm to detect the litter from the pictures and generate anchors. The pictures having achors can be viewed from the wed site where we started the mission.

## Technologies
Drone Programming,Python,Deep Learning, Amazon Wdb Services.

## Project Architecture

![image](https://github.com/chakilam-prashanth-kumar/Swatch_Campus/assets/95711596/b476a825-16f9-44e6-90b0-5b7bbf046012)

- Client is the user who is using the website for marking the way points.
  Website Link: https://swachkmit.000webhostapp.com/#
![image](https://github.com/chakilam-prashanth-kumar/Swatch_Campus/assets/95711596/d41106a3-a097-45d2-abad-1c7451f69421)
+ After all way points are marked in the website, then the user click the Start Mission button, so all the waypoints information (latitute ,longetude co-ordenates) to Ground Station as Json via Web-socket. Then Ground Station will Broadcast the instructions to the Drone using Telemetry.
+ When the drone reacted a waypoint then  camera takes the picture.
+ Camera used: GoPro Hero 9 Black
+ After completing all the waypoints then RTL command is issued by the GroundStation, so drone comes to the starting location where it started the mission.
+ After completing the mission drone uploads the pictures in the FireBase(DataBase). Notify the
Trash-Detection-Client(TDC) to start its work. 
+ TDC Fetchs the pictures from the FireBase and apply Detection algorithm on the images.
+ The model we used for detection is YOLO-v4.
+ Once the detection is completed the detected images are uploaded back to the firebase and TDC notify the user to collect the images using web-socket.
+ the WebSite will take the images from DataBase and display it to the end client.



