import numpy             as np
import matplotlib.pyplot as plt
from itertools import product
# Imports from other libraries
from .io_functions  import print_colored, check_key
from .ana_functions import generate_cut_array, get_units, get_wvf_label, shift_ADCs

#===========================================================================#
#********************** AVERAGING FUCNTIONS ********************************#
#===========================================================================# 

def average_wvfs(my_runs, info, centering="NONE", key="", label="", threshold=0, cut_label="", OPT={}, debug=False):
    '''
    \nIt calculates the average waveform of a run. Select centering:
    \n- "NONE"      -> AveWvf: each event is added without centering.
    \n- "PEAK"      -> AveWvfPeak: each event is centered according to wvf argmax. 
    \n- "THRESHOLD" -> AveWvfThreshold: each event is centered according to first wvf entry exceding a threshold.
    '''
    for run,ch in product(my_runs["NRun"], my_runs["NChannel"]):
        true_key, true_label = get_wvf_label(my_runs, "", "", debug = False)
        label = true_label
        
        if check_key(my_runs[run][ch], "MyCuts") == True:
            print("Calculating average wvf with cuts")
        else:
            generate_cut_array(my_runs)
        if check_key(my_runs[run][ch], "UnitsDict") == False:
            get_units(my_runs)

        buffer = 100  
        aux_ADC = my_runs[run][ch][key][my_runs[run][ch]["MyCuts"] == True]

        # bin_ref_peak = st.mode(np.argmax(aux_ADC,axis=1), keepdims=True) # Deprecated function st.mode()
        values, counts = np.unique(np.argmax(aux_ADC,axis=1), return_counts=True) #using the mode peak as reference
        bin_ref_peak = values[np.argmax(counts)]
        
        if centering == "NONE":
            my_runs[run][ch][label+"AveWvf"+cut_label] = [np.mean(aux_ADC,axis=0)] # It saves the average waveform as "AveWvf_*"
            if debug: print_colored("Averaging %s centered wvf: "%centering+label+"AveWvf"+cut_label, "INFO")
        
        if centering == "PEAK":
            bin_max_peak = np.argmax(aux_ADC[:,bin_ref_peak-buffer:bin_ref_peak+buffer],axis=1) 
            bin_max_peak = bin_max_peak + bin_ref_peak - buffer
            for ii in range(len(aux_ADC)):
                aux_ADC[ii] = np.roll(aux_ADC[ii],  bin_ref_peak - bin_max_peak[ii]) # It centers the waveform using the peak
            my_runs[run][ch][label+"AveWvfPeak"+cut_label] = [np.mean(aux_ADC,axis=0)]     # It saves the average waveform as "AveWvfPeak_*"
            if debug: print_colored("Averaging %s centered wvf: "+label+"AveWvfPeak"+cut_label, "INFO")
        
        if centering == "THRESHOLD":
            if threshold == 0: threshold = np.max(np.mean(aux_ADC,axis=0))/2
            # bin_ref_thld = st.mode(np.argmax(aux_ADC>threshold,axis=1), keepdims=True) # Deprecated st.mode()
            values,counts = np.unique(np.argmax(aux_ADC>threshold,axis=1), return_counts=True) #using the mode peak as reference
            bin_ref_thld = values[np.argmax(counts)] # It is an int
            bin_max_thld = np.argmax(aux_ADC[:,bin_ref_peak-buffer:bin_ref_peak+buffer]>threshold,axis=1)
            bin_max_thld = bin_max_thld + bin_ref_thld - buffer
            for ii in range(len(aux_ADC)):
                aux_ADC[ii] = np.roll(aux_ADC[ii], bin_ref_thld - bin_max_thld[ii])    # It centers the waveform using the threshold
            my_runs[run][ch][label+"AveWvfThreshold"+cut_label] = [np.mean(aux_ADC,axis=0)]  # It saves the average waveform as "AveWvfThreshold_*"
            if debug: print_colored("Averaging %s centered wvf: "+label+"AveWvfThreshold"+cut_label, "INFO")

    print_colored("Average waveform calculated", "SUCCESS")

def expo_average(my_run, alpha):
    ''' 
    \nThis function calculates the exponential average with a given alpha.
    \n**returns**: average[i+1] = (1-alpha) * average[i] + alpha * my_run[i+1]
    '''
    v_averaged = np.zeros(len(my_run)); v_averaged[0] = my_run[0]
    for i in range (len(my_run) - 1):   v_averaged[i+1] = (1-alpha) * v_averaged[i] + alpha * my_run[i+1] # e.g. alpha = 0.1  ->  average[1] = 0.9 * average[0] + 0.1 * my_run[1]
    
    return v_averaged

def unweighted_average(my_run):
    ''' 
    \nThis function calculates the unweighted average.
    \n**returns**: average[i+1] = (my_run[i] + my_run[i+1] + my_run[i+2]) / 3
    '''
    v_averaged    = np.zeros(len(my_run))
    v_averaged[0] = my_run[0]; v_averaged[-1] = my_run[-1]

    for i in range (len(my_run) - 2): v_averaged[i+1] = (my_run[i] + my_run[i+1] + my_run[i+2]) / 3 #e.g. average[1] = (my_run[0] + my_run[1] + my_run[2]) / 3
    return v_averaged

def smooth(my_run, alpha):
    ''' 
    \nThis function calculates the exponential average and then the unweighted average.
    \n**returns**: average[i+1] = (my_run[i] + my_run[i+1] + my_run[i+2]) / 3 with my_run = (1-alpha) * average[i] + alpha * my_run[i+1]
    '''
    my_run = expo_average(my_run, alpha)
    my_run = unweighted_average(my_run)
    return my_run

#===========================================================================#
#********************** INTEGRATION FUNCTIONS ******************************#
#===========================================================================# 

def find_baseline_cuts(raw):
    '''
    \nIt finds the cuts with the x-axis. It returns the index of both bins.
    \n**VARIABLES:**
    \n- raw: the .root that you want to analize.
    '''

    max = np.argmax(raw); i_idx = 0; f_idx = 0
    for j in range(len(raw[max:])):               # Before the peak
        if raw[max+j] < 0: f_idx = max+j;   break # Looks for the change of sign
    for j in range(len(raw[:max])):               # After the peak
        if raw[max-j] < 0: i_idx = max-j+1; break # Looks for the change of sign
    
    return i_idx,f_idx

def find_amp_decrease(raw,thrld):
    '''
    \nIt finds bin where the amp has fallen above a certain threshold relative to the main peak. It returns the index of both bins.
    \n**VARIABLES:**
    \n- raw: the np array that you want to analize.
    \n- thrld: the relative amp that you want to analize.
    '''

    max = np.argmax(raw); i_idx = 0; f_idx = 0
    for j in range(len(raw[max:])):                               # Before the peak
        if raw[max+j] < np.max(raw)*thrld: f_idx = max+j;   break # Looks for the change of sign (including thrld)
    for j in range(len(raw[:max])):                               # After the peak
        if raw[max-j] < np.max(raw)*thrld: i_idx = max-j+1; break # Looks for the change of sign (including thrld)

    return i_idx,f_idx

def integrate_wvfs(my_runs, info = {}, key = "", label="", cut_label="", debug = False):
    '''
    \nThis function integrates each event waveform. There are several ways to do it and we choose it with the argument "types".
    \n**VARIABLES**:
    \n- my_runs: run(s) we want to use
    \n- info: input information from .txt with DAQ characteristics and Charge Information.
    \n- key: waveform we want to integrate (by default any ADC)
    \nIn txt Charge Info part we can indicate the type of integration, the reference average waveform and the ranges we want to integrate.
    \nIf I_RANGE == -1 it fixes t0 to pedestal time and it integrates the time indicated in F_RANGE, e.g. I_RANGE = -1 F_RANGE = 6e-6 it integrates 6 microsecs from pedestal time.
    \nIf I_RANGE != -1 it integrates from the indicated time to the F_RANGE value, e.g. I_RANGE = 2.1e-6 F_RANGE = 4.3e-6 it integrates in that range.
    \nI_RANGE must have same length than F_RANGE!
    '''

    conversion_factor = info["DYNAMIC_RANGE"][0] / info["BITS"][0] # Amplification factor of the system
    channels = []; channels = np.append(channels,info["CHAN_TOTAL"])
    ch_amp = dict(zip(channels,info["CHAN_AMPLI"])) # Creates a dictionary with amplification factors according to each detector
    i_range = info["I_RANGE"] # Get initial time(s) to start the integration
    f_range = info["F_RANGE"] # Get final time(s) to finish the integration
    
    for run,ch,typ,ref in product(my_runs["NRun"], my_runs["NChannel"], info["TYPE"], info["REF"]):
        if check_key(my_runs[run][ch], "MyCuts") == False: generate_cut_array(my_runs); cut_label = ""

        print("\n--- Integrating RUN %i CH %i TYPE %s, REF %s ---"%(run,ch,typ,label+ref))
        true_key, true_label = get_wvf_label(my_runs, "", "", debug = debug)
        label = true_label

        ave = my_runs[run][ch][label+ref+cut_label] # Load the reference average waveform
        
        if check_key(my_runs[run][ch], "UnitsDict") == False:             get_units(my_runs) # If there are no units, it calculates them
        if check_key(my_runs[run][ch], label+"ChargeRangeDict") == False: my_runs[run][ch][label+"ChargeRangeDict"] = {} # Creates a dictionary with ranges for each ChargeRange entry
            
        aux_ADC = my_runs[run][ch][key]
        if true_label == "Raw": 
            aux_ADC = my_runs[run][ch]["PChannel"]*((aux_ADC.T-my_runs[run][ch][true_label+info["PED_KEY"][0]]).T)
            if label == "Raw": label = "Ana"
        for i in range(len(ave)):
            if typ == "ChargeAveRange": # Integrated charge from the average waveform
                i_idx,f_idx = find_baseline_cuts(ave[i])
                my_runs[run][ch][label+typ+cut_label] = np.sum(aux_ADC[:,i_idx:f_idx], axis = 1) # Integrated charge from the DECONVOLUTED average waveform
                
            if typ == "ChargePedRange":
                for j in range(len(f_range)):
                    i_idx = my_runs[run][ch][label+"PedLim"]
                    f_idx = i_idx + int(np.round(f_range[j]*1e-6/my_runs[run][ch]["Sampling"]))
                    my_runs[run][ch][label+typ+str(j)+cut_label] = np.sum(aux_ADC[:,i_idx:f_idx], axis = 1)

            if typ == "ChargeRange":
                for k in range(len(f_range)):
                    i_idx = int(np.round(i_range[k]*1e-6/my_runs[run][ch]["Sampling"]))
                    f_idx = int(np.round(f_range[k]*1e-6/my_runs[run][ch]["Sampling"]))
                    this_aux_ADC = shift_ADCs(aux_ADC, -np.asarray(my_runs[run][ch][label+"PeakTime"])+i_idx, debug = debug)
                    my_runs[run][ch][label+typ+str(k)+cut_label] = np.sum(this_aux_ADC[:,:f_idx], axis = 1)
            
            if debug: print_colored("Integrated wvfs according to type **%s** from %.2E to %.2E"%(typ,i_idx*my_runs[run][ch]["Sampling"],f_idx*my_runs[run][ch]["Sampling"]), "SUCCESS")
    return my_runs

        # else:
        #     [my_runs[r][ch][charge]] = pC = s * [ADC] * [V/ADC] * [A/V] * [1e12 pC/1 C]
        #     if debug: print_colored("Integrating %s from %.2E to %.2E"%(key,t0,tf),"INFO")
        #     my_runs[run][ch][label+typ+cut_label] = my_runs[run][ch]["Sampling"]*np.sum(my_runs[run][ch][key][:,i_idx:f_idx],axis=1) * conversion_factor/ch_amp[ch]*1e12

        # new_key = {typ+cut_label: [t0,tf]}
        # my_runs[run][ch]["ChargeRangeDict"].update(new_key) # Update the dictionary

# if typ.startswith("ChargeRange") and my_runs[run][ch]["Label"]=="SC" and key =="ADC": 
#     confirmation = input("**WARNING: SC** Do you want to continue with the integration ranges introduced in the input file? [y/n]]")
#     if confirmation in ["n","N","no","NO","q"]: break # Avoid range integration for SC (save time)
#     elif confirmation in ["y","Y","yes","YES"]: continue
#     else: 
#         # Create a loop to avoid wrong inputs
#         while confirmation not in ["y","Y","yes","YES","n","N","no","NO","q"]:
#             confirmation = input("Wrong input. Please, try again. [y/n] ")
#             if confirmation in ["n","N","no","NO","q"]: break # Avoid range integration for SC (save time)


# if (typ.startswith("ChargeRange") and my_runs[run][ch]["Label"]!="SC") or (typ.startswith("ChargeRange") and my_runs[run][ch]["Label"]=="SC" and confirmation not in ["n","N","no","NO","q"]):
#     for j in range(len(f_range)):
#         my_runs[run][ch][typ+str(j)+cut_label] = []
#         if i_range[j] < 0: # Integration with fixed ranges
#             t0 = np.argmax(my_runs[run][ch][ref])*my_runs[run][ch]["Sampling"] + i_range[j]
#             tf = np.argmax(my_runs[run][ch][ref])*my_runs[run][ch]["Sampling"] + f_range[j]
#         else: # Integration with custom ranges
#             t0 = i_range[j]; tf = f_range[j]
        
#         i_idx = int(np.round(t0/my_runs[run][ch]["Sampling"]))
#         f_idx = int(np.round(tf/my_runs[run][ch]["Sampling"]))
        
#         my_runs[run][ch][typ+str(j)+cut_label]= my_runs[run][ch]["Sampling"]*np.sum(my_runs[run][ch][key][:,i_idx:f_idx], axis = 1) * conversion_factor/ch_amp[ch]*1e12
#         if key == "GaussADC" or key == "WienerADC":
#             my_runs[run][ch][label+typ+str(j)+cut_label] = np.sum(my_runs[run][ch][key][:,i_idx:f_idx], axis = 1)

#         # new_key = {typ+str(j)+cut_label: [t0,tf]}
#         # my_runs[run][ch]["ChargeRangeDict"].update(new_key) # Update the dictionary

        #         print_colored("======================================================================", "SUCCESS")
        #         print_colored("Integrated wvfs according to **%s** baseline integration limits"%info["REF"][0], "SUCCESS")
        #         print_colored("========== INTEGRATION RANGES --> [%.2f, %.2f] \u03BCs =========="%(t0*1E6,tf*1E6), "SUCCESS")
        #         print_colored("======================================================================", "SUCCESS")
    
