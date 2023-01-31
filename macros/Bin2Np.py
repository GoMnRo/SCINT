import sys
sys.path.insert(0, '../')

import numpy as np
from itertools import product
from lib.io_functions import read_input_file,root2npy,load_npy,save_proccesed_variables
from lib.ana_functions import compute_peak_variables,compute_pedestal_variables
from lib.first_data_process import DumpBin2npy

input_file = input("Please select input File: ")
info = read_input_file(input_file)

runs = []; channels = []
# runs = np.append(runs,info["CALIB_RUNS"])
# runs = np.append(runs,info["LIGHT_RUNS"])
runs = np.append(runs,info["ALPHA_RUNS"])

channels = np.append(channels,info["CHAN_STNRD"])

DumpBin2npy(runs.astype(int),channels.astype(int),info=info,debug=True)
# DumpBin2npy(runs.astype(int),channels.astype(int),info=info,debug=True,compressed=False)


for run, ch in product(runs.astype(int),channels.astype(int)):
    # Start to load_runs 
    my_runs = load_npy([run],[ch])
    
    compute_peak_variables(my_runs)
    compute_pedestal_variables(my_runs)
    print(my_runs.keys())
    save_proccesed_variables(my_runs,"","../data/raw/")