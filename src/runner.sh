#!/bin/bash
if [ $# -ne 4 ]; then
	echo "please input 4 params: DataSet intersectionID testCount trialCount"
  echo "ex: Mosaic_1 135 4 4"
        exit 1;
fi

#DataSet will be the name of the directory containing all data folders
#intersectionID will be the intersection interested in analyzing
#test, trial is the test and trial to analyze
DataSet=$1
intersectionID=$2
test=$3
trial=$4
directory=$(cd ../ &&pwd)
radio="r1c"

#move to directory containing data files and create necessary file structure
cd $directory/data
mkdir -p tsharkOutput
mkdir -p decodedOutput
mkdir -p combinedOutput
mkdir -p payloadOutput

#deleting any files from previous runs
rm $directory/data/tsharkOutput/*
rm $directory/data/decodedOutput/*
rm $directory/data/combinedOutput/*
rm $directory/data/payloadOutput/*


#The OBU can transmit/receive on one of its two radios,a or c. This function will check this
#based on the size of the tx/rx pcap files
getRadioUsed() {

	radio_A_tx_cnt=$(wc -c tx_r1a.pcap | awk '{print $1}')
	radio_A_rx_cnt=$(wc -c rx_r1a.pcap | awk '{print $1}')

	if [ $radio_A_tx_cnt -gt 24 -a $radio_A_rx_cnt -gt 24 ]; then
		radio="r1a"
	fi
	echo $radio
}

#Get the timestamp and frame data into csv format
extractPackets() {
  #adjust the directory names as needed
  cd $directory/data/${DataSet}/DSRC_Mosaic_Test_${test}_Trial_${trial}

  rad=$(getRadioUsed)
  #adjust this based on which radio, a or c, transmitted and received
  #renaming pcap files to have test and trial number in their name
  mv tx_${rad}.pcap DSRC_Mosaic_Test_${test}_Trial_${trial}_tx_${rad}.pcap #tx bsm
  mv rx_${rad}.pcap DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_${rad}.pcap #rx bsm/spat/map

  #using wireshark utility tshark to extract frame time and payload into csv format
  cd $directory/data/${DataSet}/DSRC_Mosaic_Test_${test}_Trial_${trial}
  tshark -r DSRC_Mosaic_Test_${test}_Trial_${trial}_tx_${rad}.pcap --disable-protocol wsmp -Tfields -Eseparator=, -e frame.time_epoch -e data.data > \
  $directory/data/tsharkOutput/tshark_DSRC_Mosaic_Test_${test}_Trial_${trial}_tx_${rad}.csv

  tshark -r DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_${rad}.pcap --disable-protocol wsmp -Tfields -Eseparator=, -e frame.time_epoch -e data.data > \
  $directory/data/tsharkOutput/tshark_DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_${rad}.csv
}

#parse tshark output to get rid of unnecessary bytes in front of BSM/SPAT/MAP and just return payload
getPayload() {
  cd $directory/data/tsharkOutput
  for i in *
  do
    python3 $directory/src/tshark_OutputParser.py $i
  done
  mv *_payload* $directory/data/payloadOutput
}

#decode J2735 message fields
decodePackets() {
  cd $directory/data/payloadOutput

	#decoding desired fields from the transmitted BSMs, extracting additional fields can be done by editing J2735decoder.py
  for i in $(find . -name "*_tx_*")
  do
    file=$(basename -- "$i")
    fileName="${file%.*}"
    python3 $directory/src/J2735decoder.py $i 0 decoded_BSM_${fileName}.csv BSM
  done

	#decoding desired fields from the received BSMs/SPaT/MAP, extracting additional fields can be done by editing J2735decoder.py
  for i in $(find . -name "*_rx_*")
  do
    file=$(basename -- "$i")
    fileName="${file%.*}"
    python3 $directory/src/J2735decoder.py $i 0 decoded_BSM_${fileName}.csv BSM
    python3 $directory/src/J2735decoder.py $i 0 decoded_SPAT_${fileName}.csv SPAT $intersectionID
    python3 $directory/src/J2735decoder.py $i 0 decoded_MAP_${fileName}.csv MAP $intersectionID
  done

  mv *decoded* $directory/data/decodedOutput
}

#use the received spat/map files with the transmitted bsm files to figure out where vehicle was and what state the
#intersection was in
combineFiles() {
  cd $directory/src

  python3 combinedParser.py $directory/data/decodedOutput/decoded_BSM_tshark_DSRC_Mosaic_Test_${test}_Trial_${trial}_tx_${rad}_payload.csv \
  $directory/data/decodedOutput/decoded_BSM_tshark_DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_${rad}_payload.csv \
  $directory/data/decodedOutput/decoded_SPAT_tshark_DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_${rad}_payload.csv \
  $directory/data/decodedOutput/decoded_MAP_tshark_DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_${rad}_payload.csv

  mv *_combined* $directory/data/combinedOutput
}

#renaming tx/rx files in case script needs to be rerun on the same data set
renameRawFiles() {
	cd $directory/data/${DataSet}/DSRC_Mosaic_Test_${test}_Trial_${trial}

	mv DSRC_Mosaic_Test_${test}_Trial_${trial}_tx_r1a.pcap tx_r1a.pcap
	mv DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_r1a.pcap rx_r1a.pcap
	mv DSRC_Mosaic_Test_${test}_Trial_${trial}_tx_r1c.pcap tx_r1c.pcap
	mv DSRC_Mosaic_Test_${test}_Trial_${trial}_rx_r1c.pcap rx_r1c.pcap
}

processing(){
  extractPackets
  getPayload
  decodePackets
  combineFiles
	renameRawFiles
 }

processing
