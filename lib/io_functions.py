import os
import matplotlib.pyplot as plt
import numpy as np
import uproot
import copy
import stat

from itertools import product

#===========================================================================#
#************************** INPUT FILE *************************************#
#===========================================================================#

def read_input_file(input, path = "../input/", debug = False):
    """
    Obtain the information stored in a .txt input file to load the runs and channels needed.
    """

    # Using readlines()
    file = open(path+input+".txt", 'r')
    lines = file.readlines()
    info = dict()
    NUMBERS = ["MUONS_RUNS","LIGHT_RUNS","ALPHA_RUNS","CALIB_RUNS","CHAN_STNRD","CHAN_CALIB","CHAN_POLAR"]
    DOUBLES = ["SAMPLING"]
    STRINGS = ["MONTH","RAW_DATA","OV_LABEL","CHAN_LABEL"]
    # Strips the newline character
    for line in lines:
        for LABEL in DOUBLES:
            if line.startswith(LABEL):
                info[LABEL] = []
                numbers = line.split(" ")[1].strip("\n")
                for i in numbers.split(","):
                    try:
                        info[LABEL].append(float(i))
                    except ValueError: 
                        if debug == True:
                            print("Error when reading: ", info[LABEL])

                    if debug: print(info[LABEL])
        for LABEL in NUMBERS:
            if line.startswith(LABEL):
                info[LABEL] = []
                numbers = line.split(" ")[1].strip("\n")
                for i in numbers.split(","):
                    try:
                        info[LABEL].append(int(i))
                    except ValueError: 
                        if debug == True:
                            print("Error when reading: ", info[LABEL])
                    
                    if debug: print(info[LABEL])
        for LABEL in STRINGS:
            if line.startswith(LABEL):
                info[LABEL] = []
                numbers = line.split(" ")[1].strip("\n")
                for i in numbers.split(","):
                    try:
                        info[LABEL].append(i)
                    except ValueError:
                        if debug == True:
                            print("Error when reading: ", info[LABEL])
                    
                    if debug: print(info[LABEL])
    print("\n")
    print(info.keys())
    print("\n")

    return info

#===========================================================================#
#************************* RAW TO NUMPY ************************************#
#===========================================================================#

def root2npy(runs, channels, info={}, debug=False): ### ACTUALIZAR COMO LA DE BINARIO ###
    """
    Dumper from .root format to npy tuples. 
    Input are root input file path and npy outputfile as strings. 
    \n Depends on uproot, awkward and numpy. 
    \n Size increases x2 times. 
    """

    in_path  = "../data/"+info["MONTH"][0]+"/raw/"
    out_path = "../data/"+info["MONTH"][0]+"/npy/"
    for run, ch in product (runs.astype(int),channels.astype(int)):
        i = np.where(runs == run)[0][0]
        j = np.where(channels == ch)[0][0]

        in_file  = "run"+str(run).zfill(2)+"_ch"+str(ch)+".root"
        out_file = "run"+str(run).zfill(2)+"_ch"+str(ch)+".npy"
        
        try:
            f = uproot.open(in_path+in_file)
            my_dict = {}
            
            if debug:
                print("----------------------")
                print("Dumping file:", in_path+in_file)
            
            for branch in f["IR02"].keys():
                if debug: print("dumping brach:",branch)
                my_dict[branch]=f["IR02"][branch].array().to_numpy()
            
            # additional useful info
            my_dict["RawADC"] = my_dict["ADC"]
            del my_dict["ADC"]
            my_dict["NBinsWvf"] = my_dict["RawADC"][0].shape[0]
            my_dict["Sampling"] = info["SAMPLING"][0]
            my_dict["Label"] = info["CHAN_LABEL"][j]
            my_dict["RawPChannel"] = int(info["CHAN_POLAR"][j])

            np.save(out_path+out_file,my_dict)
            
            if debug:
                print(my_dict.keys())
                print("Saved data in:" , out_path+out_file)
                print("----------------------\n")

        except FileNotFoundError:
            print("--- File %s was not foud!!! \n"%in_file)

def binary2npy(runs, channels, info={}, debug=True, compressed=True, header_lines=6, force=False):
    """
    Dumper from binary format to npy tuples. 
    Input are binary input file path and npy outputfile as strings. 
    \n Depends numpy. 
    """

    in_path  = "../data/"+info["MONTH"][0]+"/raw/"
    out_path = "../data/"+info["MONTH"][0]+"/npy/"

    for run, ch in product(runs.astype(int),channels.astype(int)):
        i = np.where(runs == run)[0][0]
        j = np.where(channels == ch)[0][0]

        in_file = "run"+str(run).zfill(2)+"/wave"+str(ch)+".dat"
        out_folder = "run"+str(run).zfill(2)+"_ch"+str(ch)+"/"

        try:
            os.mkdir(out_path+out_folder)
            os.chmod(out_path+out_folder, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

        except FileExistsError: print("DATA STRUCTURE ALREADY EXISTS") 

        header     = np.fromfile(in_path+in_file, dtype='I')[:6] #read first event header
        NSamples   = int(header[0]/2-header_lines*2)
        Event_size = header_lines*2+NSamples
        data       = np.fromfile(in_path+in_file, dtype='H')
        N_Events   = int( data.shape[0]/Event_size )

        if debug:
            print("#####################################################################")
            print("Header:",header)
            print("Waveform Samples:",NSamples)
            print("Event_size(wvf+header):",Event_size)
            print("N_Events:",N_Events)
            print("#####################################################################\n")
            
        #reshape everything, delete unused header
        ADC = np.reshape(data,(N_Events,Event_size))[:,header_lines*2:]
        
        branches = ["RawADC", "NBinsWvf", "Sampling", "Label", "RawPChannel"]
        content  = [ADC, ADC.shape[0], info["SAMPLING"][0], info["CHAN_LABEL"][j], int(info["CHAN_POLAR"][j])]
        files=os.listdir(out_path+out_folder)

        for i, branch in enumerate(branches):
            try:
                if branch+".npz" in files and force == True:
                    print("File (%s.npz) alredy exists. OVERWRITTEN"%branch)
                    os.remove(out_path+out_folder+branch+".npz") 
                    np.savez_compressed(out_path+out_folder+branch+".npz", content[i])
                    os.chmod(out_path+out_folder+branch+".npz", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

                    if not compressed:
                        os.remove(out_path+out_folder+branch+".npy") 
                        np.save(out_path+out_folder+branch+".npy", content[i])
                        os.chmod(out_path+out_folder+branch+".npy", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

                
                elif branch+".npz" in files and force == False:
                    print("File (%s.npz) alredy exists."%branch)
                    continue

                else:
                    np.savez_compressed(out_path+out_folder+branch+".npz", content[i])
                    os.chmod(out_path+out_folder+branch+".npz", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

                    if not compressed:
                        np.save(out_path+out_folder+branch+".npy", content[i])
                        os.chmod(out_path+out_folder+branch+".npy", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

                if debug:
                    print(branch)
                    print("Saved data in:" , out_path+out_folder+branch+".npx")
                    print("----------------------\n")
                
            except FileNotFoundError:
                print("--- File %s was not foud!!! \n"%in_file)
        

#===========================================================================#
#***************************** KEYS ****************************************#
#===========================================================================#

def check_key(OPT, key):
    """ 
    Checks if the given key is included in the dictionary OPT.
    \n Returns a bool. (True if it finds the key)
    """

    try:
        OPT[key]
        return True    
    except KeyError:
        return False

def print_keys(my_runs):
    """
    Prints the keys of the run_dict which can be accesed with run_dict[runs][channels][BRANCH] 
    """

    try:
        for run, ch in product(my_runs["NRun"], my_runs["NChannel"]):
            print("------------------------------------------------------------------------------------------------------------------------------------------------------")
            print("Dictionary keys --> ",list(my_runs[run][ch].keys()))
            print("------------------------------------------------------------------------------------------------------------------------------------------------------\n")
    except KeyError:
        return print("Empty dictionary. No keys to print.")

def delete_keys(my_runs, keys):
    """
    Delete the keys list introduced as 2nd variable
    """

    for run, ch, key in product(my_runs["NRun"], my_runs["NChannel"], keys):
        try:
            del my_runs[run][ch][key]
        except KeyError:
            print("*EXCEPTION: ",run, ch, key," key combination is not found in my_runs")   

def get_preset_list(my_run, path, folder, preset, option, debug = False):
    """
    Return as output presets lists for load/save npy files.
    Variables:
        my_run: my_runs[run][ch]
        path: saving path
        folder: saving in/out folder
        preset: 
            (a) "ALL": all the existing keys/branches
            (b) "ANA": Only Ana keys/branches (removing RAW info)
            (c) "RAW": Only Raw information i.e loaded from Raw2Np + Raw* keys
        option:
            (a) "LOAD": takes the os.listdir(path+folder) as brach_list (IN)
            (b) "SAVE": takes the my_run.keys() as branch list (OUT)
    """

    dict_option = dict()
    dict_option["LOAD"] = os.listdir(path+folder)
    dict_option["SAVE"] = my_run.keys()

    if preset == "ALL":
        branch_list = dict_option[option]

    elif preset == "ANA":
        branch_list = dict_option[option]
        aux = []
        for key in branch_list:
            if not "Raw" in key: aux.append(key)
        branch_list = aux

    elif preset == "RAW":
        branch_list = dict_option[option]
        aux = ["NBinsWvf", "Sampling", "Label"]
        for key in branch_list:
            if "Raw" in key: aux.append(key)
        branch_list = aux

    if debug: print("\nPreset branch_list:", branch_list)
    return branch_list

#===========================================================================#
#************************** LOAD/SAVE NPY **********************************#
#===========================================================================# 

def load_npy(runs, channels, preset="", branch_list = [], info={}, debug = False, compressed=True):
    """
    Structure: run_dict[runs][channels][BRANCH] 
    \n Loads the selected channels and runs, for simplicity, all runs must have the same number of channels
    \n Presets can be used to only load a subset of desired branches. ALL is default.
    """

    path = "../data/"+info["MONTH"][0]+"/npy/"

    my_runs = dict()
    my_runs["NRun"]     = runs
    my_runs["NChannel"] = channels

    for run in runs:
        my_runs[run]=dict()
        for ch in channels:
            my_runs[run][ch]=dict()
            in_folder="run"+str(run).zfill(2)+"_ch"+str(ch)+"/"
            if not branch_list:
                branch_list = get_preset_list(my_runs[run][ch], path, in_folder, preset, "LOAD", debug)

            for branch in branch_list:   
                try:
                    my_runs[run][ch][branch.replace(".npz","")] = np.load(path+in_folder+branch.replace(".npz","")+".npz",allow_pickle=True, mmap_mode="w+")["arr_0"]           
                    if not compressed:
                        my_runs[run][ch][branch.replace(".npy","")] = np.load(path+in_folder+branch.replace(".npy","")+".npy",allow_pickle=True, mmap_mode="w+").item()

                    if debug: print("\nLoaded %s run with keys:"%branch,my_runs.keys())
                    if debug: print("-----------------------------------------------")
                except FileNotFoundError: print("\nRun", run, ", channels" ,ch," --> NOT LOADED (FileNotFound)")
            print("-> DONE!\n")
    return my_runs

def save_proccesed_variables(my_runs, preset = "", branch_list = [], info={}, force=False, debug = False, compressed=True):
    """
    Does exactly what it says, no RawWvfs here
    """

    aux = copy.deepcopy(my_runs) # Save a copy of my_runs with all modifications and remove the unwanted branches in the copy
    path = "../data/"+info["MONTH"][0]+"/npy/"

    for run in aux["NRun"]:
        for ch in aux["NChannel"]:
            out_folder = "run"+str(run).zfill(2)+"_ch"+str(ch)+"/"
            files=os.listdir(path+out_folder)
            if not branch_list:
               branch_list = get_preset_list(my_runs[run][ch],path, out_folder, preset, "SAVE", debug)

            for key in branch_list:
                key = key.replace(".npz","")

                if key+".npz" in files and force == False:
                    print("File (%s.npz) alredy exists"%key)
                    continue
                elif key+".npz" in files and force == True:
                    print("File (%s.npz) OVERWRITTEN "%key)
                    os.remove(path+out_folder+key+".npz")
                    np.savez_compressed(path+out_folder+key+".npz",aux[run][ch][key])
                    os.chmod(path+out_folder+key+".npz", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

                else:
                    print("Saving NEW file: %s.npz"%key)
                    print(path+out_folder+key+".npz")
                    np.savez_compressed(path+out_folder+key+".npz",aux[run][ch][key])
                    os.chmod(path+out_folder+key+".npz", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

                    if not compressed:
                        np.save(path+out_folder+key+".npy",aux[run][ch][key])
                        os.chmod(path+out_folder+key+".npy", stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
    del my_runs
    
#DEPREACTED??#
def copy_single_run(my_runs, runs, channels, keys):
    my_run = dict()
    my_run["NRun"] = []
    my_run["NChannel"] = []
    for run, ch, key in product(runs,channels,keys):
        try:
            my_run["NRun"].append(run)
            my_run["NChannel"].append(ch)
            my_run[run] = dict()
            my_run[run][ch] = dict()
            my_run[run][ch][key] = my_runs[run][ch][key]
        except KeyError:
            print(run,ch,key," key combination is not found in my_runs")
    return my_run