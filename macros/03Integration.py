# ---------------------------------------------------------------------------------------------------------------------- #
#  ========================================= RUN:$ python3 03Integration.py TEST ======================================= #
# This macro will c   #
# Ideally we want to work in /pnfs/ciemat.es/data/neutrinos/FOLDER and so we mount the folder in our computer with:      #
# $ sshfs USER@pcaeXYZ.ciemat.es:/pnfs/ciemat.es/data/neutrinos/FOLDER ../data  --> making sure empty data folder exists #
# ---------------------------------------------------------------------------------------------------------------------- #

import sys; sys.path.insert(0, '../'); from lib import *; print_header()

try:
    input_file = sys.argv[1]
except IndexError:
    input_file = input("Please select input File: ")

info = read_input_file(input_file)
runs = []; channels = []
runs = np.append(runs,info["CALIB_RUNS"])
runs = np.append(runs,info["LIGHT_RUNS"])
runs = np.append(runs,info["ALPHA_RUNS"])
runs = np.append(runs,info["MUONS_RUNS"])

channels = np.append(channels,info["CHAN_TOTAL"])

for run, ch in product(runs.astype(int),channels.astype(int)):
    
    my_runs = load_npy([run],[ch],preset="ANA",info=info,compressed=True)
    print_keys(my_runs)

    ## Align indivual waveforms + Average ##
    # average_wvfs(my_runs,centering="PEAK") # Compute average wvfs VERY COMPUTER INTENSIVE!
    # average_wvfs(my_runs,centering="THRESHOLD") # Compute average wvfs EVEN MORE COMPUTER INTENSIVE!

    ## Charge Integration ##
    integrate_wvfs(my_runs, info = info, key="ADC") # Compute charge according to selected average wvf from input file ("AveWvf", "AveWvfPeak", "AveWvfThreshold")
    # charge_nevents(my_runs)
    save_proccesed_variables(my_runs,"CHARGE",info=info, force=True)