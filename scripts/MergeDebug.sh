#!/bin/bash

# RUN --> sh ../scripts/MergeDebug.sh 
# Make sure you have RUNS{1,9,25,29}+CH{0,6} in data/raw/*.root #

echo "\n----------------------------------------------------------------------------------------------"
echo "\n----------------------------- (: WELCOME TO THE DEBUG SCRIPT :) ------------------------------"
echo "\n We recommend to use the input/MergeDebug.txt file to try the macros before merging branches."
echo "\n----------------------------------------------------------------------------------------------"
echo "\n"

# 00Raw2Np.py --> loads raw data + save into /data/MONTH/npy/
echo "\n------------------ Testing Root2Np.py ------------------"
python3 ../macros/00Raw2Np.py MergeDebug
echo "\n------ Expected output{Saved data in: ../data/MONTH/npy/runXX_chY/RAW_NAME_BRANCH.npy}. Everything OK ------"


#01PreProcess.py --> pre-process raw waveforms and save PEDESTAL/PEAK variables
echo "\n------------------ Testing Process.py ------------------"
python3 ../macros/01PreProcess.py MergeDebug
echo "\n------ Expected output{Saved data in: ../data/MONTH/npy/runXX_chY/NAME_BRANCH.npy}. Everything OK ------"

# 02Process.py --> process wvfs with raw pedesatal/peak info to get the ANA wvf with BASELINE/PCH changed
echo "\n------------------ Testing Average.py ------------------"
python3 ../macros/02Process.py MergeDebug
echo "\n------ Expected output{Saved data in: ../data/MONTH/npy/runXX_chY/ANA_NAME_BRANCH.npy}. Everything OK ------"


#03Calibration.py --> calibrate (calibration runs) and obtain gain values in txt
echo "\n------------------ Testing Calibration.py ------------------"
python3 ../macros/03Calibration.py MergeDebug
echo "\n------ Expected output{FIT_PLOT + SPE gauss parameters X Y Z + ../fit_data/gain_chX.txt}. Everything OK ------"


#0XVisTests.py --> visualize event by event the selected runs&channels
echo "\n------------------ Testing Vis.py ------------------"
python3 ../macros/0XVisTests.py MergeDebug 1 0,6
echo "\n------ Expected output{PLOT}. Everything OK ------"


#04Decovolution.py --> perform deconvolution
echo "\n------------------ Testing Vis.py ------------------"
python3 ../macros/04Decovolution.py MergeDebug
echo "\n------ Expected output{PLOT}. Everything OK ------"