#!/bin/bash
if [ $# -ne 4 ]; then
	echo "please input 4 params: DataSet intersectionID testCount trialCount"
  echo "ex: Mosaic_1 135 4 4"
        exit 1;
fi
DataSet=$1
intersectionID=$2
testCount=$3
trialCount=$4
directory=$(cd ../ &&pwd)

cd $directory/data
mkdir -p tsharkOutput
mkdir -p decodedOutput
mkdir -p combinedOutput
mkdir -p payloadOutput

extractPackets() {
	#i should be how many tests are to be analyzed in the data set
	#j should be the range of trials
  for i in $(eval echo "{1..$testCount}")
  do
    for j in $(eval echo "{1..$trialCount}")
      do
				#adjust the directory names as needed
        cd $directory/data/${DataSet}/DSRC_Mosaic_Test_${i}_Trial_${j}

				#adjust this based on which radio, a or c, transmitted and received
        mv tx_r1a.pcap DSRC_Mosaic_Test_${i}_Trial_${j}_tx_r1a.pcap #tx bsm
        mv rx_r1a.pcap DSRC_Mosaic_Test_${i}_Trial_${j}_rx_r1a.pcap #rx bsm/spat/map

				#using wireshark utility tshark to extract frame time and payload into csv format
        cd $directory/data/${DataSet}/DSRC_Mosaic_Test_${i}_Trial_${j}
        tshark -r DSRC_Mosaic_Test_${i}_Trial_${j}_tx_r1a.pcap --disable-protocol wsmp -Tfields -Eseparator=, -e frame.time_epoch -e data.data > \
        $directory/data/tsharkOutput/tshark_DSRC_Mosaic_Test_${i}_Trial_${j}_tx_r1a.csv

        tshark -r DSRC_Mosaic_Test_${i}_Trial_${j}_rx_r1a.pcap --disable-protocol wsmp -Tfields -Eseparator=, -e frame.time_epoch -e data.data > \
        $directory/data/tsharkOutput/tshark_DSRC_Mosaic_Test_${i}_Trial_${j}_rx_r1a.csv
      done
  done
}

getPayload() {
  cd $directory/data/tsharkOutput
  #parse tshark output to get rid of unnecessary bytes in front of BSM/SPAT/MAP
  for i in *
  do
    python3 $directory/src/tshark_OutputParser.py $i
  done
  mv *_payload* $directory/data/payloadOutput
}

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

combineFiles() {
  cd $directory/src

  for i in $(eval echo "{1..$testCount}")
  do
    for j in $(eval echo "{1..$trialCount}")
    do
      python3 combinedParser.py $directory/data/decodedOutput/decoded_BSM_tshark_DSRC_Mosaic_Test_${i}_Trial_${j}_tx_r1a_payload.csv \
      $directory/data/decodedOutput/decoded_BSM_tshark_DSRC_Mosaic_Test_${i}_Trial_${j}_rx_r1a_payload.csv \
      $directory/data/decodedOutput/decoded_SPAT_tshark_DSRC_Mosaic_Test_${i}_Trial_${j}_rx_r1a_payload.csv \
      $directory/data/decodedOutput/decoded_MAP_tshark_DSRC_Mosaic_Test_${i}_Trial_${j}_rx_r1a_payload.csv
    done
  done

  mv *_combined* $directory/data/combinedOutput
}

processing(){
  extractPackets
  getPayload
  decodePackets
  combineFiles
 }

processing
