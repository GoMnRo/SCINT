# ---------------------------------------------------------------------------------------------------------------------- #
#  =========================================== RUN:$ python3 01Process.py TEST ========================================= #
# This macro will process peak/pedestal variables (PRE-PROCESS) and save the AnaADC with the new baseline/polarity ...   #
# Ideally we want to work in /pnfs/ciemat.es/data/neutrinos/FOLDER and so we mount the folder in our computer with:      #
# $ sshfs USER@pcaeXYZ.ciemat.es:/pnfs/ciemat.es/data/neutrinos/FOLDER ../data  --> making sure empty data folder exists #
# ---------------------------------------------------------------------------------------------------------------------- #

#Falta hacer todos los imports con el mismo fichero#
import sys
sys.path.insert(0, '../')

import numpy as np
from lib.io_functions  import read_input_file,load_npy,delete_keys,save_proccesed_variables
from lib.ana_functions import compute_pedestal_variables,compute_peak_variables,compute_ana_wvfs,insert_variable
from lib.wvf_functions import average_wvfs,integrate_wvfs
from itertools import product

if sys.argv[1]: input_file = sys.argv[1]
else          : input_file = input("Please select input File: ")

info = read_input_file(input_file)
runs = []; channels = []
runs = np.append(runs,info["CALIB_RUNS"])
# runs = np.append(runs,info["LIGHT_RUNS"])
# runs = np.append(runs,info["ALPHA_RUNS"])
# runs = np.append(runs,info["MUONS_RUNS"])

channels = np.append(channels,info["CHAN_STNRD"])

""" To-Do: Avoid using loop in this macro. Maybe "ADC" type dict can be loaded in lazy mode """

# PRE-PROCESS RAW #
for run, ch in product(runs.astype(int),channels.astype(int)):
    # Start to load_runs 
    my_runs = load_npy([run],[ch],preset="RAW",info=info,compressed=True)
    
    compute_peak_variables(my_runs)
    compute_pedestal_variables(my_runs)
    print(my_runs.keys())
    save_proccesed_variables(my_runs,"ALL",info=info, force=True)


# PROCESS WAVEFORMS (Run in loop to avoid memory issues)
for run, ch in product(runs.astype(int),channels.astype(int)):
    
    # my_runs = load_npy([run],[ch],branches="ALL", info=info, compressed=True)
    my_runs = load_npy([run],[ch],preset="ALL",info=info,compressed=True)

    print(my_runs[run][ch].keys())
    compute_ana_wvfs(my_runs,debug=False)

    delete_keys(my_runs,['PeakAmp', 'PeakTime', 'PedSTD', 'PedMean', 'PedMax', 'PedMin', 'PedLim','PChannel'])  # Delete raw peak and pedestal variables
    insert_variable(my_runs,[1,1,1,1],"PChannel")                                                               # Change polarity!
    
    compute_peak_variables(my_runs,key="AnaADC")                                                                # Compute new peak variables
    compute_pedestal_variables(my_runs,key="AnaADC",debug=True)
    
    delete_keys(my_runs,["ADC"])

    average_wvfs(my_runs)
    integrate_wvfs(my_runs,["ChargeAveRange"],"AveWvf",["DAQ", 250],[0,100])
    
    save_proccesed_variables(my_runs,"ALL",info=info, force=True)