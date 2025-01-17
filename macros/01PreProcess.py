import sys; sys.path.insert(0, '../'); from lib import *
default_dict = {"runs":["CALIB_RUNS","LIGHT_RUNS","ALPHA_RUNS","MUONS_RUNS","NOISE_RUNS"],"channels":["CHAN_TOTAL"],"key":["ANA_KEY"]}
user_input = initialize_macro("01PreProcess",["input_file","debug"],default_dict=default_dict, debug=True)
info = read_input_file(user_input["input_file"][0], debug=user_input["debug"])
### 01PreProcess
for run, ch in product(np.asarray(user_input["runs"]).astype(int),np.asarray(user_input["channels"]).astype(int)):
    ### Load
    my_runs = load_npy([run],[ch], info, preset=info["LOAD_PRESET"][1], compressed=True, debug=user_input["debug"])
    ### Compute
    compute_peak_variables(my_runs, key=user_input["key"][0], label="", debug=user_input["debug"])
    compute_pedestal_variables(my_runs, key=user_input["key"][0], label="", debug=user_input["debug"]) # Checking the best window in the pretrigger
    average_wvfs(my_runs, info=info, key=user_input["key"][0], centering="NONE", debug=user_input["debug"])
    ### Remove branches to exclude from saving
    delete_keys(my_runs,[user_input["key"][0],"TimeStamp","Sampling"]) # Delete previous peak and pedestal variables
    save_proccesed_variables(my_runs, info, preset=info["SAVE_PRESET"][1], force=True, debug=user_input["debug"])
    ### Free memory
    del my_runs
    gc.collect()
