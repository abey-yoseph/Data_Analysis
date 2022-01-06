import json
import sys
import pandas as pd
from csv import writer
from csv import reader
import math

inFile = sys.argv[1]
fileName = inFile.split(".")

#the three strings below indicate the start of the payload of a MAP,SPaT, or BSM
map_substr = "0012"
spat_substr = "0013"
bsm_substr = "0014"

#searches for one of the three substrings in the extracted tshark data and returns the J2735 message
def getPayload(row):
    try:
        if map_substr in row[1]:
            map_index = row[1].find(map_substr)
            map = row[1][map_index:]

            return map
        elif spat_substr in row[1]:
            spat_index = row[1].find(spat_substr)
            spat_length = len(row[1])
            if "mk5" in fileName[0] and "rx" in fileName[0]:
                spat = row[1][spat_index:spat_length-8]
            else:
                spat = row[1][spat_index:]

            return spat
        elif bsm_substr in row[1]:
            bsm_index = row[1].find(bsm_substr)
            bsm = row[1][bsm_index:]

            return bsm
    except:
        print("Error getting payload for: " + str(row[1]))


#read the tshark file and create a file containing timestamps and payloads
tsharkOutputFile = pd.read_csv(f'{fileName[0]}.csv')
df_data = {'timestamp': tsharkOutputFile.iloc[:,0], 'payload': tsharkOutputFile.apply(lambda row: getPayload(row), axis=1)}
payload = pd.DataFrame(data=df_data)
payload.to_csv(f'{fileName[0]}_payload.csv', index=False)
