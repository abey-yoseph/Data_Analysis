import pandas as pd
import numpy as np
import sys
from csv import writer
from csv import reader
import difflib
import math
import geopy.distance

#read in necessary input files
bsm_txFile = sys.argv[1] #BSM TX OBU file
bsm_rxFile = sys.argv[2] #BSM RX OBU file (shuttle)
spat_rxFile = sys.argv[3] #SPAT RX OBU file
map_rxFile = sys.argv[4] #MAP RX OBU file

testNum = bsm_txFile.split("_")[6]
trialNum = bsm_txFile.split("_")[8]

#calculate the time left before crossing the intersection
def timeToIntersection(distance, velocity_initial):
    #using two v=x/t, t=x/v
    return distance/velocity_initial

#calculate the distance between two points using gps coordinates
def distanceBetween(txLat, txLong, rxLat, rxLong):
    txCoordinates = (float(txLat), float(txLong))
    rxCoordinates = (float(rxLat), float(rxLong))
    return geopy.distance.distance(txCoordinates, rxCoordinates).m

#calculate the time left in the phase
def phaseTime(moy, endTime):
    endTimeConverted = endTime*0.1
    minutesInCurrentHour = moy % 60
    secondsInCurrentHour = minutesInCurrentHour*60

    if endTimeConverted < secondsInCurrentHour:
        timeLeft = (60*(60-minutesInCurrentHour))+endTimeConverted

    else:
        timeLeft = endTimeConverted-secondsInCurrentHour

    return timeLeft

with open(bsm_txFile, "r") as bsmTx, open(bsm_rxFile, "r") as bsmRx, open(spat_rxFile, "r") as spatRx, open(map_rxFile, "r") as mapRx, \
open("Test_"+testNum+"_Trial_"+trialNum+"_combined.csv", 'w', newline='') as write_obj:
    #converting input files to lists
    csv_bsm_tx_reader = reader(bsmTx)
    csv_bsm_rx_reader = reader(bsmRx)
    csv_spat_rx_reader = reader(spatRx)
    csv_map_rx_reader = reader(mapRx)

    next(csv_bsm_tx_reader)
    next(csv_bsm_rx_reader)
    next(csv_spat_rx_reader)
    next(csv_map_rx_reader)

    bsmTxRows = list(csv_bsm_tx_reader)
    bsmRxRows = list(csv_bsm_rx_reader)
    spatRxRows = list(csv_spat_rx_reader)
    mapRxRows = list(csv_map_rx_reader)

    #get the static GPS coordinates of the intersection of interest
    intersection_lat = mapRxRows[1][2]
    intersection_long = mapRxRows[1][3]

    previousDistance = 0

    csv_writer = writer(write_obj)
    csv_writer.writerow(["shuttle_bsm_rx_time", "shuttle_lat", "shuttle_long", "shuttle_speed(m/s)", "shuttle_accel(m/s^2)", "vehicle_bsm_tx_time",
    "vehicle_obu_tx_lat", "vehicle_obu_tx_long", "vehicle_speed(m/s)", "vehicle_acceleration(m/s^2)", "distance_to_intersection(m)",
    "time_to_intersection(s)", "signalgroup2_state", "signalgroup2_phase_minEndTime(s)", "signalgroup2_phase_maxEndTime(s)",
    "signalgroup4_state", "signalgroup4_phase_minEndTime(s)", "signalgroup4_phase_maxEndTime(s)",
    "signalgroup6_state", "signalgroup6_phase_minEndTime(s)", "signalgroup6_phase_maxEndTime(s)",
    "signalgroup8_state", "signalgroup8_phase_minEndTime(s)", "signalgroup8_phase_maxEndTime(s)"])

    #start by iterating through the transmitted BSM files
    for i in range(0, len(bsmTxRows)):
        vehicle_tx_time = float(bsmTxRows[i][0])
        vehicle_tx_lat = float(bsmTxRows[i][1])
        vehicle_tx_long = float(bsmTxRows[i][2])
        vehicle_speed = float(bsmTxRows[i][3])
        vehicle_accel = float(bsmTxRows[i][4])
        time = "n/a"
        difference = 1000
        index = 0

        #find where the test vehicle was located when shuttle transmitted bsm
        for j in range(0, len(bsmRxRows)):
            shuttle_rxTime = float(bsmRxRows[j][0])
            temp = vehicle_tx_time - shuttle_rxTime
            if (temp > 0 and temp < difference):
                difference = temp
                index = j

        shuttle_rxTime = float(bsmRxRows[index][0])
        shuttle_lat = float(bsmRxRows[index][1])
        shuttle_long = float(bsmRxRows[index][2])
        shuttle_speed = float(bsmRxRows[index][3])
        shuttle_accel = float(bsmRxRows[index][4])

        #get the distance to the intersection based on the vehicle's current GPS coordinates and the coordinates of the
        #intersection from the MAP message
        distanceToIntersection = distanceBetween(vehicle_tx_lat, vehicle_tx_long, intersection_lat, intersection_long)

        #get the time to the intersection if the vehicle is moving towards the intersection
        if vehicle_speed != 0 and distanceToIntersection <= previousDistance:
            time = timeToIntersection(distanceToIntersection, vehicle_speed)

        previousDistance = distanceToIntersection

        difference2 = 1000
        index2 = 0
        lastSpatRxRow = 0
        #get the closest spat message in time to the transmitted BSM and extract signal phase information
        for k in range(lastSpatRxRow+1, len(spatRxRows)):
            spat_rxTime = float(spatRxRows[k][0])
            temp2 = vehicle_tx_time - spat_rxTime
            if (temp2 > 0 and temp2 < difference2):
                difference2 = temp2
                index2 = k

            #get the 4 signal states for the spat message of interest
            signalgroup2_state = spatRxRows[index2][2]
            signalgroup2_phase_minEndTime = float(spatRxRows[index2][3])
            signalgroup2_phase_maxEndTime = float(spatRxRows[index2][4])
            signalgroup4_state = spatRxRows[index2][5]
            signalgroup4_phase_minEndTime = float(spatRxRows[index2][6])
            signalgroup4_phase_maxEndTime = float(spatRxRows[index2][7])
            signalgroup6_state = spatRxRows[index2][8]
            signalgroup6_phase_minEndTime = float(spatRxRows[index2][9])
            signalgroup6_phase_maxEndTime = float(spatRxRows[index2][10])
            signalgroup8_state = spatRxRows[index2][11]
            signalgroup8_phase_minEndTime = float(spatRxRows[index2][12])
            signalgroup8_phase_maxEndTime = float(spatRxRows[index2][13])
            moy = float(spatRxRows[index2][14])

            #calculate min and max time left in the 4 signal phases
            signalgroup2_phase_minEndTime_calculated = phaseTime(moy, signalgroup2_phase_minEndTime)
            signalgroup2_phase_maxEndTime_calculated = phaseTime(moy, signalgroup2_phase_maxEndTime)
            signalgroup4_phase_minEndTime_calculated = phaseTime(moy, signalgroup4_phase_minEndTime)
            signalgroup4_phase_maxEndTime_calculated = phaseTime(moy, signalgroup4_phase_maxEndTime)
            signalgroup6_phase_minEndTime_calculated = phaseTime(moy, signalgroup6_phase_minEndTime)
            signalgroup6_phase_maxEndTime_calculated = phaseTime(moy, signalgroup6_phase_maxEndTime)
            signalgroup8_phase_minEndTime_calculated = phaseTime(moy, signalgroup8_phase_minEndTime)
            signalgroup8_phase_maxEndTime_calculated = phaseTime(moy, signalgroup8_phase_maxEndTime)

            lastSpatRxRow = index2

        #write all desired information to a csv
        csv_writer.writerow([shuttle_rxTime, shuttle_lat, shuttle_long, shuttle_speed, shuttle_accel, vehicle_tx_time, vehicle_tx_lat,
        vehicle_tx_long, vehicle_speed, vehicle_accel, distanceToIntersection, time, signalgroup2_state, signalgroup2_phase_minEndTime_calculated, signalgroup2_phase_maxEndTime_calculated,
        signalgroup4_state, signalgroup4_phase_minEndTime_calculated, signalgroup4_phase_maxEndTime_calculated,
        signalgroup6_state, signalgroup6_phase_minEndTime_calculated, signalgroup6_phase_maxEndTime_calculated,
        signalgroup8_state, signalgroup8_phase_minEndTime_calculated, signalgroup8_phase_maxEndTime_calculated])
