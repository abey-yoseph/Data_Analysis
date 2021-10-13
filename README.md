Directory Setup:
1. Clone the "/src" directory in the desired location on your local machine.
2. Create a "data" directory in the same location.
3. Place all raw data folders in the created "data" directory.

The data analysis scripts are executed by using the "runner.sh" bash script. 
The "runner.sh" expects 4 parameters: 
1. The name of the data set to be analyzed
2. The intersection ID of the intersection be analyzed
3. The total number of tests
4. The total number of trials per test

The csv output of the data analysis will be in the "/data/combinedOutput" directory.
