#!/usr/bin/env python
from binascii import hexlify, unhexlify
import J2735
import json
import sys
import csv
import math

intersection = 0

def extract_values(obj, key):
    """Pull all values of specified key from nested JSON."""
    arr = []

    def extract(obj, arr, key):
        """Recursively search for values of key in JSON tree."""
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    extract(v, arr, key)
                elif k == key:
                    arr.append(v)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return arr

    results = extract(obj, arr, key)
    return results

## read from file and print time for only asked id
##usage pydecoder filename  id outputfile

#print("usage pydecoder filename id outputfile J2735msg[BSM/MAP/SPAT]")

if (len(sys.argv) < 4):
    print("Incomplete Arguments");
    exit(1)

fp1=open(sys.argv[1],'r')
id=int(sys.argv[2])
fout=open(sys.argv[3],'w')#,0)
msgid=""
if(sys.argv[4] == "BSM"):
    msgid="0014"
    fout.write("time,latitude,longitude,speed(m/s),accel_long(m/s^2),hex\n")
elif(sys.argv[4]=="SPAT"):
    intersection = int(sys.argv[5])
    msgid="0013"
    fout.write("time,intersectionID,group2_state,group2_minEndTime,group2_maxEndTime,group4_state,group4_minEndTime,group4_maxEndTime,group6_state,group6_minEndTime,group6_maxEndTime,group8_state,group8_minEndTime,group8_maxEndTime,moy,hex\n")
elif(sys.argv[4]=="MAP"):
    intersection = int(sys.argv[5])
    msgid="0012"
    fout.write("time,intersectionID,laneLat,laneLong,laneWidth,hex\n")

fp= csv.reader(fp1,delimiter=',')
list1=list(fp)

for dt in list1:

    if(dt[1][0:4]==msgid):
        msg = J2735.DSRC.MessageFrame
        #print("hex: " + dt[1] + " byte length: " + str(len(dt[1])))
        try:
            msg.from_uper(unhexlify(dt[1]))
        except:
            continue

        if (msgid == "0013"):
            # if (msg()['value'][1]['intersections'][0]['id']['id'] == intersection):
            #     print("Intersection: " + str(intersection))

            intersectionID = msg()['value'][1]['intersections'][0]['id']['id']
            if intersectionID == intersection:
                group2_eventState = msg()['value'][1]['intersections'][0]['states'][1]['state-time-speed'][0]['eventState']
                group2_minEndTime = float(msg()['value'][1]['intersections'][0]['states'][1]['state-time-speed'][0]['timing']['minEndTime']) #tenths of a second
                group2_maxEndTime = float(msg()['value'][1]['intersections'][0]['states'][1]['state-time-speed'][0]['timing']['maxEndTime']) #tenths of a second
                group4_eventState = msg()['value'][1]['intersections'][0]['states'][3]['state-time-speed'][0]['eventState']
                group4_minEndTime = float(msg()['value'][1]['intersections'][0]['states'][3]['state-time-speed'][0]['timing']['minEndTime']) #tenths of a second
                group4_maxEndTime = float(msg()['value'][1]['intersections'][0]['states'][3]['state-time-speed'][0]['timing']['maxEndTime']) #tenths of a second
                group6_eventState = msg()['value'][1]['intersections'][0]['states'][5]['state-time-speed'][0]['eventState']
                group6_minEndTime = float(msg()['value'][1]['intersections'][0]['states'][5]['state-time-speed'][0]['timing']['minEndTime']) #tenths of a second
                group6_maxEndTime = float(msg()['value'][1]['intersections'][0]['states'][5]['state-time-speed'][0]['timing']['maxEndTime']) #tenths of a second
                group8_eventState = msg()['value'][1]['intersections'][0]['states'][7]['state-time-speed'][0]['eventState']
                group8_minEndTime = float(msg()['value'][1]['intersections'][0]['states'][7]['state-time-speed'][0]['timing']['minEndTime']) #tenths of a second
                group8_maxEndTime = float(msg()['value'][1]['intersections'][0]['states'][7]['state-time-speed'][0]['timing']['maxEndTime']) #tenths of a second
                moy = msg()['value'][1]['intersections'][0]['moy']

                fout.write(str(dt[0])+','+str(intersectionID)+','+str(group2_eventState)+','+str(group2_minEndTime)+','+str(group2_maxEndTime)
                +','+str(group4_eventState)+','+str(group4_minEndTime)+','+str(group4_maxEndTime)+','+str(group6_eventState)+','+str(group6_minEndTime)
                +','+str(group6_maxEndTime)+','+str(group8_eventState)+','+str(group8_minEndTime)+','+str(group8_maxEndTime)+','+str(moy)+','+str(dt[1])+'\n')

        elif (msgid == "0012"):
            intersectionID = msg()['value'][1]['intersections'][0]['id']['id']
            if intersectionID == intersection:
                lat = msg()['value'][1]['intersections'][0]['refPoint']['lat']
                long = msg()['value'][1]['intersections'][0]['refPoint']['long']
                laneWidth = msg()['value'][1]['intersections'][0]['laneWidth']
                fout.write(str(dt[0])+','+str(intersectionID)+','+str(lat/10000000.0)+','+str(long/10000000.0)+','+str(laneWidth)+','+str(dt[1])+'\n')

        elif (msgid == "0014"):
            lat= msg()['value'][1]['coreData']['lat']
            long = msg()['value'][1]['coreData']['long']
            speed = msg()['value'][1]['coreData']['speed']
            speed_converted = speed*0.02 #m/s
            accel_long = msg()['value'][1]['coreData']['accelSet']['long']
            accel_long_converted = accel_long*0.01 #m^s^2

            fout.write(str(dt[0])+','+str(lat/10000000.0)+','+str(long/10000000.0)+','+str(speed_converted)+','+str(accel_long_converted)+','+str(dt[1])+'\n')
