# ---------------------------------------------------------------------------------------------------------------------- #
#  ========================================= RUN:$ python3 03Integration.py TEST ======================================= #
# This macro will calculate integration parametes of all individual wvfs, to be used in subsequent steps of calibration, #
# charge and deconvolution.                                                                                              #
# Ideally we want to work in /pnfs/ciemat.es/data/neutrinos/FOLDER and so we mount the folder in our computer with:      #
# $ sshfs USER@pcaeXYZ.ciemat.es:/pnfs/ciemat.es/data/neutrinos/FOLDER ../data  --> making sure empty data folder exists #
# ---------------------------------------------------------------------------------------------------------------------- #

import sys; sys.path.insert(0, '../'); from lib import *; print_header()
try:               input_file = sys.argv[1]
except IndexError: input_file = input("Please select input File: ")

info = read_input_file(input_file)
runs = []; channels = []
runs = np.append(runs,info["CALIB_RUNS"])
runs = np.append(runs,info["LIGHT_RUNS"])
runs = np.append(runs,info["ALPHA_RUNS"])
runs = np.append(runs,info["MUONS_RUNS"])

channels = np.append(channels,info["CHAN_TOTAL"])

# my_runs = load_npy(runs.astype(int),channels.astype(int),preset="ANA",info=info,compressed=True)

for run, ch in product(runs.astype(int),channels.astype(int)):
    
    my_runs = load_npy([run],[ch],preset=str(info["LOAD_PRESET"][3]),info=info,compressed=True)
    # my_runs = load_npy([run],[ch],preset="EVA",info=info,compressed=True)
    # cut_min_max(my_runs, ["PedSTD"], {"PedSTD": [-1,7.5]})
    # cut_min_max(my_runs, ["PeakAmp"], {"PeakAmp": [2400,6500]})
    # cut_min_max(my_runs, ["PeakTime"], {"PeakTime": [3.8e-6,4e-6]})
    # cut_lin_rel(my_runs, ["PeakAmp","ChargeAveRange"])

    # cut_peak_finder(my_runs, ["ADC"], 2)

    ## Align indivual waveforms + Average ##
    # average_wvfs(my_runs,centering="NONE") # Compute average wvfs VERY COMPUTER INTENSIVE!
    # average_wvfs(my_runs,centering="PEAK") # Compute average wvfs VERY COMPUTER INTENSIVE!
    # average_wvfs(my_runs,centering="THRESHOLD") # Compute average wvfs EVEN MORE COMPUTER INTENSIVE!

    ## Charge Integration ##
    integrate_wvfs(my_runs, info = info) # Compute charge according to selected average wvf from input file ("AveWvf", "AveWvfPeak", "AveWvfThreshold")
    # charge_nevents(my_runs)

    # delete_keys(my_runs,["GaussADC"]) # Delete branches to avoid overwritting
    save_proccesed_variables(my_runs,preset=str(info["SAVE_PRESET"][3]),info=info, force=True)
    del my_runs
    gc.collect()