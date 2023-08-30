#================================================================================================================================================#
# In this library we have all the functions related with visualization. They are mostly used in 0XVis*.py macros but can be included anywhere !! #
#================================================================================================================================================#

import math
import numpy             as np
import matplotlib.pyplot as plt
from matplotlib.colors           import LogNorm
from matplotlib.cm               import viridis
from itertools                   import product
from scipy.signal                import find_peaks
from scipy.ndimage.interpolation import shift

from .io_functions  import print_colored

def vis_npy(my_run, keys, evt_sel = -1, same_plot = False, OPT = {}, debug = False):
    '''
    This function is a event visualizer. It plots individual events of a run, indicating the pedestal level, pedestal std and the pedestal calc limit.
    We can interact with the plot and pass through the events freely (go back, jump to a specific event...)
    
    **VARIABLES:**

    - my_run: run(s) we want to check
    - KEYS: choose between ADC or AnaADC to see raw (as get from ADC) or Analyzed events (starting in 0 counts), respectively. Type: List
    - OPT: several options that can be True or False. Type: List

      (a) MICRO_SEC: if True we multiply Sampling by 1e6
      (b) NORM: True if we want normalized waveforms
      (c) LOGY: True if we want logarithmic y-axis
      (d) SHOW_AVE: if computed and True, it will show average
      (e) SHOW_PARAM: True if we want to check calculated parameters (pedestal, amplitude, charge...)
      (f) CHARGE_KEY: if computed and True, it will show the parametre value
      (g) PEAK_FINDER: True if we want to check how many peaks are

    - evt_sel: choose the events we want to see. If -1 all events are displayed, if 0 only uncutted events are displayed, if 1 only cutted events are displayed
    - same_plot: True if we want to plot different channels in the SAME plot
    '''

    # Imports from other libraries
    from .io_functions  import check_key,print_colored
    from .fig_config    import figure_features
    from .ana_functions import get_wvf_label


    figure_features()
    charge_key = "ChargeAveRange"
    if check_key(OPT, "CHARGE_KEY"): charge_key = OPT["CHARGE_KEY"]
    norm_ave = 1
    buffer = 100

    ch_list = my_run["NChannel"]
    nch = len(my_run["NChannel"])
    axs = []
    true_key, true_label = get_wvf_label(my_run, "", "", debug = False)

    for run, key in product(my_run["NRun"],keys):
        plt.ion()
        if same_plot == False:
            if nch < 4:
                fig, ax = plt.subplots(nch ,1, figsize = (10,8))
                if nch == 1: axs.append(ax)
                else: axs = ax
            else:
                fig, ax = plt.subplots(2, math.ceil(nch/2), figsize = (10,8))
                axs = ax.T.flatten()
        else:
            fig, ax = plt.subplots(1 ,1, figsize = (8,6))
            axs = ax
        idx = 0
        for i in range(len(my_run[run][ch_list[0]][true_key])):
            try:
                skip = 0
                for ch in ch_list:
                    if evt_sel == 0 and my_run[run][ch]["MyCuts"][idx] == False: skip = 1; break # To Skip Cutted events!!
                    if evt_sel == 1 and my_run[run][ch]["MyCuts"][idx] == True:  skip = 1; break # To Get only Cutted events!!
                if skip == 1: idx = idx +1; continue
            except: pass

            fig.supxlabel(r'Time [s]')
            fig.supylabel("ADC Counts")
            min = []
            raw = []
            norm_raw = [1]*nch # Generates a list with the norm correction for std bar
            for j in range(nch):
                if (key == "RawADC"):
                    min.append(np.argmin(my_run[run][ch_list[j]][key][idx]))
                    raw.append(my_run[run][ch_list[j]][key][idx])
                    ped = np.mean(my_run[run][ch_list[j]][key][idx][:min[j]-buffer])
                    std = np.std(my_run[run][ch_list[j]][key][idx][:min[j]-buffer])
                    label = "Raw"
                    if debug: print_colored("Using '%s' label"%label, "DEBUG")

                elif(key == "AnaADC"):
                    print_colored("AnaADC not saved but we compute it now :)", "WARNING")
                    min.append(np.argmax(my_run[run][ch_list[j]][true_key][idx]))
                    ana = my_run[run][ch_list[j]]["RawPChannel"]*((my_run[run][ch_list[j]]["RawADC"][idx].T-my_run[run][ch_list[j]]["RawPedMean"][idx]).T)
                    raw.append(ana)
                    ped = 0
                    std = my_run[run][ch_list[j]]["AnaPedSTD"][idx]
                    label = "Ana"
                    if debug: print_colored("Using '%s' label"%label, "DEBUG")

                elif("ADC" in str(key)):
                    min.append(np.argmax(my_run[run][ch_list[j]][key][idx]))
                    raw.append(my_run[run][ch_list[j]][key][idx])
                    ped = 0
                    std = np.std(my_run[run][ch_list[j]][key][idx][:min[j]-buffer])
                    label = key.replace("ADC","")
                    if debug: print_colored("Using '%s' label"%label, "DEBUG")

                elif("Ave" in str(key)):
                    min.append(np.argmax(my_run[run][ch_list[j]][key][idx]))
                    raw.append(my_run[run][ch_list[j]][key][idx])
                    ped = 0
                    std = np.std(my_run[run][ch_list[j]][key][idx][:min[j]-buffer])
                    label = key.replace("Ave","")
                    if debug: print_colored("Using '%s' label"%label, "DEBUG")

                if check_key(OPT, "NORM") == True and OPT["NORM"] == True:
                    norm_raw[j] = (np.max(raw[j]))
                    raw[j] = raw[j]/np.max(raw[j])

                sampling = my_run[run][ch_list[j]]["Sampling"] # To reset the sampling to its initial value (could be improved)
                if check_key(OPT, "MICRO_SEC") == True and OPT["MICRO_SEC"]==True:
                    fig.supxlabel(r'Time [$\mu$s]')
                    my_run[run][ch_list[j]]["Sampling"] = my_run[run][ch_list[j]]["Sampling"]*1e6

                if same_plot == False:
                    if check_key(OPT, "LOGY") == True and OPT["LOGY"] == True:
                        axs[j].semilogy()
                        std = 0 # It is ugly if we see this line in log plots
                    # fig.tight_layout(h_pad=2) # If we want more space betweeb subplots. We avoid small vertical space between plots            
                    axs[j].plot(my_run[run][ch_list[j]]["Sampling"]*np.arange(len(raw[j])),raw[j],label="RAW_WVF", drawstyle = "steps", alpha = 0.95, linewidth=1.2)
                    axs[j].grid(True, alpha = 0.7)
                    try:
                        axs[j].scatter(my_run[run][ch_list[j]]["Sampling"]*my_run[run][ch_list[j]][label+"PeakTime"][idx],my_run[run][ch_list[j]][label+"PeakAmp"][idx],c="tab:red", alpha = 0.8)
                        axs[j].plot(my_run[run][ch_list[j]]["Sampling"]*np.array([my_run[run][ch_list[j]][label+"PedLim"],my_run[run][ch_list[j]][label+"PedLim"]]),np.array([ped+4*std,ped-4*std])/norm_raw[j],c="red",lw=2., alpha = 0.8)
                        axs[j].plot(my_run[run][ch_list[j]]["Sampling"]*np.array([my_run[run][ch_list[j]][label+"PedStart"][idx],my_run[run][ch_list[j]][label+"PedStart"][idx]]),np.array([ped+4*std,ped-4*std])/norm_raw[j],c="k",lw=1., alpha = 0.8)
                        axs[j].plot(my_run[run][ch_list[j]]["Sampling"]*np.array([my_run[run][ch_list[j]][label+"PedEnd"][idx],my_run[run][ch_list[j]][label+"PedEnd"][idx]]),np.array([ped+4*std,ped-4*std])/norm_raw[j],c="k",lw=1., alpha = 0.8)
                        axs[j].axhline((ped)/norm_raw[j],c="k",alpha=.55)
                        axs[j].axhline((ped+std)/norm_raw[j],c="k",alpha=.5,ls="--"); axs[j].axhline((ped-std)/norm_raw[j],c="k",alpha=.5,ls="--")
                    except KeyError: print_colored("Run preprocess please!", "ERROR")
                    axs[j].set_title("Run {} - Ch {} - Event Number {}".format(run,ch_list[j],idx),size = 14)
                    axs[j].xaxis.offsetText.set_fontsize(14) # Smaller fontsize for scientific notation
                    
                    if check_key(OPT, "SHOW_AVE") == True:   
                        try:
                            ave_key = OPT["SHOW_AVE"]
                            ave = my_run[run][ch_list[j]][ave_key][0]
                            if OPT["NORM"] == True and OPT["NORM"] == True:
                                ave = ave/np.max(ave)
                            if check_key(OPT, "ALIGN") == True and OPT["ALIGN"] == True:
                                ref_max_idx = np.argmax(raw[j])
                                idx_move = np.argmax(ave)
                                ave = shift(ave, ref_max_idx-idx_move, cval = 0)
                            axs[j].plot(my_run[run][ch_list[j]]["Sampling"]*np.arange(len(ave)),ave,alpha=.5,label="AVE_WVF_%s"%ave_key, drawstyle = "steps")             
                        except KeyError: print_colored("Run has not been averaged!", "ERROR")

                    if check_key(OPT, "LEGEND") == True and OPT["LEGEND"]: axs[j].legend()

                    if check_key(OPT, "PEAK_FINDER") == True and OPT["PEAK_FINDER"]:
                        # These parameters must be modified according to the run...
                        if check_key(my_run[run][ch_list[j]], "AveWvfSPE") == False: thresh = my_run[run][ch_list[j]]["PedMax"][idx] + 0.5*my_run[run][ch_list[j]]["PedMax"][idx]
                        else:                                                        thresh = np.max(my_run[run][ch_list[j]]["AveWvfSPE"])*3/4
                        
                        wdth = 4; prom = 0.01; dist  = 30
                        axs[j].axhline(thresh,c="k", alpha=.6, ls = "dotted")
                        peak_idx, _ = find_peaks(raw[j], height = thresh, width = wdth, prominence = prom, distance=dist)
                        for p in peak_idx: axs[j].scatter(my_run[run][ch_list[j]]["Sampling"]*p,raw[j][p],c="tab:red", alpha = 0.9)

                    try:
                        if my_run[run][ch_list[j]]["MyCuts"][idx] == False:
                            figure_features(tex = False)
                            axs[j].text(0.5,0.5, s = 'CUT', fontsize = 100, horizontalalignment='center',verticalalignment='center',
                                        transform = axs[j].transAxes, color = 'red', fontweight = "bold", alpha = 0.5)
                            figure_features()
                    except: pass
                
                else:
                    if check_key(OPT, "LOGY") == True and OPT["LOGY"]:
                        axs.semilogy()
                        std = 0 # It is ugly if we see this line in log plots
                    axs.plot(my_run[run][ch_list[j]]["Sampling"]*np.arange(len(raw[j])),raw[j], drawstyle = "steps", alpha = 0.95, linewidth=1.2,label = "Ch {} ({})".format(ch_list[j],my_run[run][ch_list[j]]["Label"]).replace("#"," "))
                    axs.grid(True, alpha = 0.7)
                    try: 
                        axs.scatter(my_run[run][ch_list[j]]["Sampling"]*my_run[run][ch_list[j]][label+"PeakTime"][idx],my_run[run][ch_list[j]][label+"PeakAmp"][idx],c="tab:red", alpha = 0.8)
                        axs.plot(my_run[run][ch_list[j]]["Sampling"]*np.array([my_run[run][ch_list[j]][label+"PedLim"],my_run[run][ch_list[j]][label+"PedLim"]]),np.array([ped+4*std,ped-4*std])/norm_raw[j],c="red",lw=2., alpha = 0.8)
                        axs.plot(my_run[run][ch_list[j]]["Sampling"]*np.array([my_run[run][ch_list[j]][label+"PedStart"][idx],my_run[run][ch_list[j]][label+"PedStart"][idx]]),np.array([ped+4*std,ped-4*std])/norm_raw[j],c="k",lw=1., alpha = 0.8)
                        axs.plot(my_run[run][ch_list[j]]["Sampling"]*np.array([my_run[run][ch_list[j]][label+"PedEnd"][idx],my_run[run][ch_list[j]][label+"PedEnd"][idx]]),np.array([ped+4*std,ped-4*std])/norm_raw[j],c="k",lw=1., alpha = 0.8)
                    except KeyError: print_colored("Run preprocess please!", "ERROR")
                    axs.set_title("Run {} - Event Number {}".format(run,idx),size = 14)
                    axs.xaxis.offsetText.set_fontsize(14)
                    
                    if check_key(OPT, "SHOW_AVE") == True:   
                        try:
                            ave_key = OPT["SHOW_AVE"]
                            ave = my_run[run][ch_list[j]][ave_key][0]
                            if OPT["NORM"] == True and OPT["NORM"] == True: ave = ave/np.max(ave)
                            if check_key(OPT, "ALIGN") == True and OPT["ALIGN"] == True:
                                ref_max_idx, = np.where(ave == np.max(ave))
                                idx, = np.where(ave == np.max(ave))
                                ave = shift(ave, ref_max_idx-idx, cval = 0)
                            axs.plot(my_run[run][ch_list[j]]["Sampling"]*np.arange(len(ave)),ave,alpha=.5,label="AVE_WVF_%s"%ave_key)             
                        except KeyError: print_colored("Run has not been averaged!", "ERROR")

                    if check_key(OPT, "LEGEND") == True and OPT["LEGEND"]: axs.legend()
                    if check_key(OPT, "PEAK_FINDER") == True and OPT["PEAK_FINDER"]:
                        # These parameters must be modified according to the run...
                        thresh = my_run[run][ch_list[j]]["PedMax"][idx]
                        wdth = 4; prom = 0.01; dist = 40
                        axs.axhline(thresh,c="salmon", alpha=.6, ls = "dotted")
                        # peak_idx, _ = find_peaks(raw[j], height = thresh, width = wdth, prominence = prom, distance=dist)
                        peak_idx, _ = find_peaks(raw[j], height = thresh)       
                        for p in peak_idx: axs.scatter(my_run[run][ch_list[j]]["Sampling"]*p,raw[j][p],c="tab:red", alpha = 0.9)

                    try:
                        if my_run[run][ch_list[j]]["MyCuts"][idx] == False:
                            figure_features(tex = False)
                            axs.text(0.5,0.5, s = 'CUT', fontsize = 100, horizontalalignment='center',verticalalignment='center',
                                        transform = axs.transAxes, color = 'red', fontweight = "bold", alpha = 0.5)
                            figure_features()
                    except: pass
                    
                if check_key(OPT, "SHOW_PARAM") == True and OPT["SHOW_PARAM"]:
                    print_colored("\nEvent Number {} from RUN_{} CH_{} ({})".format(idx,run,ch_list[j],my_run[run][ch_list[j]]["Label"]), "white", bold=True)
                    try: print("- Sampling: {:.0E}".format(sampling))
                    except KeyError: print_colored("Variable not found!", color="ERROR")
                    try: print("- Pedestal mean: {:.2E}".format(my_run[run][ch_list[j]][label+"PedMean"][idx]))
                    except KeyError: print_colored("Pedestal mean not found!", color="ERROR")
                    try: print("- Pedestal std: {:.4f}".format(my_run[run][ch_list[j]][label+"PedSTD"][idx]))
                    except KeyError: print_colored("Pedestal std not found!", color="ERROR")
                    try: print("- Pedestal min: {:.4f}\t Pedestal max {:.4f}".format(my_run[run][ch_list[j]][label+"PedMin"][idx],my_run[run][ch_list[j]][label+"PedMax"][idx]))
                    except KeyError: print_colored("Pedestal min/max not found!", color="ERROR")
                    try: print("- Pedestal time limit: {:.4E}".format(my_run[run][ch_list[j]]["Sampling"]*my_run[run][ch_list[j]][label+"PedLim"]))
                    except KeyError: print_colored("Pedestal time limit not found!", color="ERROR")
                    try: print("- Pedestal window start: {:.4E}".format(my_run[run][ch_list[j]]["Sampling"]*my_run[run][ch_list[j]][label+"PedStart"][idx]))
                    except KeyError: print_colored("window start not found!", color="ERROR")
                    try: print("- Pedestal window end: {:.4E}".format(my_run[run][ch_list[j]]["Sampling"]*my_run[run][ch_list[j]][label+"PedEnd"][idx]))
                    except KeyError: print_colored("window end not found!", color="ERROR")
                    try: print("- Max peak amplitude: {:.4f}".format(my_run[run][ch_list[j]][label+"PeakAmp"][idx]))
                    except KeyError: print_colored("Max peak amplitude not found!", color="ERROR")
                    try: print("- Max peak time: {:.2E}".format(my_run[run][ch_list[j]][label+"PeakTime"][idx]*my_run[run][ch_list[j]]["Sampling"]))
                    except KeyError: print_colored("Max peak time not found!", color="ERROR")
                    try:    print("-",OPT["CHARGE_KEY"],"{:.2E}".format(my_run[run][ch_list[j]][OPT["CHARGE_KEY"]][idx]))
                    except:
                        if check_key(OPT,"CHARGE_KEY"): print_colored("- Charge: has not been computed for key %s!"%OPT["CHARGE_KEY"], "WARNING")
                        else: print("- Charge: default charge key has not been computed")
                    try:      print("- Peak_idx:",peak_idx*my_run[run][ch_list[j]]["Sampling"])
                    except:
                        if not check_key(OPT,"PEAK_FINDER"): print("")
                my_run[run][ch_list[j]]["Sampling"] = sampling    

            tecla = input("\nPress q to quit, p to save plot, r to go back, n to choose event or any key to continue: ")

            if   tecla == "q": break
            elif tecla == "r": idx = idx-1
            elif tecla == "n":
                ev_num = int(input("Enter event number: "))
                idx = ev_num
                if idx > len(my_run[run][ch_list[j]][true_key]): idx = len(my_run[run][ch_list[j]][true_key])-1; print_colored("\nBe careful! There are %i in total"%idx, "WARNING", bold=True)
            elif tecla == "p":
                fig.savefig('run{}_evt{}.png'.format(run,idx), dpi = 500)
                idx = idx+1
            else: idx = idx + 1
            if idx == len(my_run[run][ch_list[j]][true_key]): break
            try: [axs[j].clear() for j in range (nch)]
            except: axs.clear()
        try: [axs[j].clear() for j in range (nch)]
        except: axs.clear()
        plt.close()

def vis_compare_wvf(my_run, keys, compare="RUNS", OPT = {}):
    '''
    This function is a waveform visualizer. It plots the selected waveform with the key and allow comparisson between runs/channels.
    
    **VARIABLES:**

    - my_run: run(s) we want to check
    - KEYS: waveform to plot (AveWvf, AveWvdSPE, ...). Type: List
    - OPT: several options that can be True or False.  Type: List

      (a) MICRO_SEC: if True we multiply Sampling by 1e6
      (b) NORM: True if we want normalized waveforms
      (c) LOGY: True if we want logarithmic y-axis

    - compare: 

      (a) "RUNS" to get a plot for each channel and the selected runs. Type: String
      (b) "CHANNELS" to get a plot for each run and the selected channels. Type: String
    '''

    # Imports from other libraries
    from .io_functions  import check_key
    from .fit_functions import fit_wvfs
    from .fig_config    import figure_features

    figure_features()
    r_list = my_run["NRun"]
    ch_list = my_run["NChannel"]
    nch = len(my_run["NChannel"])
    axs = []
    
    if compare == "CHANNELS": a_list = r_list;  b_list = ch_list 
    if compare == "RUNS":     a_list = ch_list; b_list = r_list 

    for a in a_list:
        if compare == "CHANNELS": run = a
        if compare == "RUNS":      ch = a

        plt.ion()
        fig, ax = plt.subplots(1 ,1, figsize = (8,6))
        axs = ax

        fig.supxlabel(r'Time [s]')
        fig.supylabel("ADC Counts")
        # fig.supylabel("Normalized Amplitude")
        norm_raw = [1]*nch # Generates a list with the norm correction for std bar
        counter = 0
        ref_max_idx = -1
        for b in b_list:
            if compare == "CHANNELS": ch = b; label = "Channel {} ({}) - {}".format(ch,my_run[run][ch]["Label"],keys[counter]); title = "Average Waveform - Run {}".format(run)
            if compare == "RUNS":    run = b; label = "Run {} - {}".format(run,keys[counter]); title = "Average Waveform - Ch {} ({})".format(ch,my_run[run][ch]["Label"]).replace("#"," ")
            if   len(keys) == 1: ave = my_run[run][ch][keys[counter]][0]
            elif len(keys) > 1:  ave = my_run[run][ch][keys[counter]][0]; counter = counter + 1

            norm_ave = np.max(ave)
            sampling = my_run[run][ch]["Sampling"] # To reset the sampling to its initial value (could be improved)
            thrld = 1e-6
            if check_key(OPT,"NORM") == True and OPT["NORM"] == True:          ave = ave/norm_ave
            if check_key(OPT, "MICRO_SEC") == True and OPT["MICRO_SEC"]==True: fig.supxlabel(r'Time [$\mu$s]'); sampling = my_run[run][ch]["Sampling"]*1e6
            if check_key(OPT, "LOGY") == True and OPT["LOGY"] == True:         axs.semilogy()
            if check_key(OPT, "ALIGN") == True and OPT["ALIGN"] == True:
                ref_threshold = np.argmax(ave>np.max(ave)*2/3)
                if ref_max_idx == -1: ref_max_idx = ref_threshold
                ave = np.roll(ave, ref_max_idx-ref_threshold)

            if check_key(OPT, "SCINT_FIT") == True and OPT["SCINT_FIT"]==True:
                fit, popt = fit_wvfs(my_run, "Scint", thrld, fit_range=[200,4000],sigma = 1e-8, a_fast = 1e-8, a_slow = 1e-6,OPT={"SHOW":False}, in_key=[keys[counter]])
                axs.plot(my_run[run][ch]["Sampling"]*np.arange(len(fit)),fit*norm_ave, linestyle="--", alpha = 0.95, linewidth=1.0, label = label+" (Fit)")
            
            axs.plot(sampling*np.arange(len(ave)),ave, drawstyle = "steps", alpha = 0.95, linewidth=1.2, label = label.replace("#"," "))

        axs.grid(True, alpha = 0.7)
        axs.set_title(title,size = 14)
        axs.xaxis.offsetText.set_fontsize(14) # Smaller fontsize for scientific notation
        if check_key(OPT, "LEGEND") == True and OPT["LEGEND"]: axs.legend()
       
        tecla   = input("\nPress q to quit, p to save plot and any key to continue: ")
        counter = 0
        if tecla   == "q": break 
        elif tecla == "p": fig.savefig('AveWvf_Ch{}.png'.format(ch), dpi = 500); counter += 1
        else: counter += 1
        if   counter > len(ch_list): break
        elif counter > len(r_list):  break
        try: [axs[ch].clear() for ch in range (nch)]
        except: axs.clear()
        plt.close()   

def vis_var_hist(my_run, key, compare = "NONE", percentile = [0.1, 99.9], OPT = {"SHOW": True}, select_range = False, debug = False):
    '''
    This function takes the specified variables and makes histograms. The binning is fix to 600, so maybe it is not the appropriate.
    Outliers are taken into account with the percentile. It discards values below and above the indicated percetiles.
    It returns values of counts, bins and bars from the histogram to be used in other function.
    
    **VARIABLES:**

    - my_run: run(s) we want to check
    - keys: variables we want to plot as histograms. Type: List

      (a) PeakAmp: histogram of max amplitudes of all events. The binning is 1 ADC. There are not outliers.
      (b) PeakTime: histogram of times of the max amplitude in events. The binning is the double of the sampling. There are not outliers.
      (c) Other variable: any other variable. Here we reject outliers.
      
    - percentile: percentile used for outliers removal
    
    WARNING! Maybe the binning stuff should be studied in more detail.
    '''

    # Imports from other libraries
    from .io_functions  import check_key
    from .ana_functions import generate_cut_array, get_units
    from .fig_config    import figure_features, add_grid

    figure_features()
    all_counts = []
    all_bins = []
    all_bars = []
    r_list = my_run["NRun"]
    ch_list = my_run["NChannel"]
    if compare == "CHANNELS": a_list = r_list;  b_list = ch_list 
    if compare == "RUNS":     a_list = ch_list; b_list = r_list
    if compare == "NONE":     a_list = r_list;  b_list = ch_list

    data = []
    for a in a_list:
        if compare != "NONE": plt.ion(); fig, ax = plt.subplots(1,1, figsize = (8,6)); add_grid(ax)

        for b in b_list:
            if compare == "CHANNELS": run = a; ch = b; title = "Run_{} ".format(run); label = "{}".format(my_run[run][ch]["Label"]).replace("#"," ") + " (Ch {})".format(ch)
            if compare == "RUNS":     run = b; ch = a; title = "{}".format(my_run[run][ch]["Label"]).replace("#"," ") + " (Ch {})".format(ch); label = "Run {}".format(run)
            if compare == "NONE":     run = a; ch = b; title = "Run_{} - {}".format(run,my_run[run][ch]["Label"]).replace("#"," ") + " (Ch {})".format(ch); label = ""
            
            # print(my_run[run][ch]["MyCuts"] == True)
            if check_key(my_run[run][ch], "MyCuts") == False:    generate_cut_array(my_run,debug=True)
            if check_key(my_run[run][ch], "UnitsDict") == False: get_units(my_run)
            
            if compare == "NONE": fig, ax = plt.subplots(1,1, figsize = (8,6)); add_grid(ax)
            
            binning = 0
            if check_key(OPT, "ACCURACY") == True: binning = OPT["ACCURACY"]

            for k in key:
                # Debug the following line
                if debug: print_colored("Plotting variable: ", k, color="INFO")
                aux_data = np.asarray(my_run[run][ch][k])[np.asarray(my_run[run][ch]["MyCuts"] == True)]
                aux_data = aux_data[~np.isnan(aux_data)]
                
                if k == "PeakAmp":
                    data = aux_data
                    max_amp = np.max(data)
                    # binning = int(max_amp)+1
                    if binning == 0: binning = 1000
                
                elif k == "PeakTime":
                    data = my_run[run][ch]["Sampling"]*aux_data
                    if binning == 0: binning = int(my_run[run][ch]["NBinsWvf"]/10)
                    
                else:
                    data = aux_data
                    ypbot = np.percentile(data, percentile[0]); yptop = np.percentile(data, percentile[1])
                    ypad = 0.2*(yptop - ypbot)
                    ymin = ypbot - ypad; ymax = yptop + ypad
                    data = [i for i in data if ymin<i<ymax]
                    if binning == 0: binning = 400 # FIXED VALUE UNTIL BETTER SOLUTION

                density = False
                y_label = "Counts"
                if check_key(OPT, "NORM") == True and OPT["NORM"] == True:
                    y_label = "Normalized Counts"
                    density = True

                if len(key) > 1:
                    fig.supxlabel(my_run[run][ch]["UnitsDict"][k]);
                    fig.supylabel(y_label)
                    label = label + " - " + k
                    fig.suptitle(title)
                else:
                    fig.supxlabel(k+" ("+my_run[run][ch]["UnitsDict"][k]+")"); 
                    fig.supylabel(y_label)
                    fig.suptitle(title + " - {} histogram".format(k))

                if select_range:
                    x1 = -1e6
                    while x1 == -1e6:
                        try:    x1 = float(input("xmin: ")); x2 = float(input("xmax: "))
                        except: x1 = -1e6 
                    counts, bins, bars = ax.hist(data, bins = int(binning), label=label, histtype="step", range=(x1,x2), density=density) # , zorder = 2 f
                else:counts, bins, bars = ax.hist(data,binning, label=label, histtype="step", density=density) # , zorder = 2 f
                    
                label = label.replace(" - " + k,"")
                all_counts.append(counts)
                all_bins.append(bins)
                all_bars.append(bars)
            
            if check_key(OPT, "LEGEND") == True and OPT["LEGEND"]:     ax.legend()
            if check_key(OPT, "LOGY") == True and OPT["LOGY"] == True: ax.semilogy()
            if check_key(OPT,"SHOW") == True and OPT["SHOW"] == True and compare == "NONE":
                plt.ion()
                plt.show()
                while not plt.waitforbuttonpress(-1): pass
                plt.close()
        if check_key(OPT,"SHOW") == True and OPT["SHOW"] == True and compare != "NONE":
            plt.show()
            while not plt.waitforbuttonpress(-1): pass
            plt.close()

    return all_counts, all_bins, all_bars

def vis_two_var_hist(my_run, keys, compare = "NONE", percentile = [0.1, 99.9], select_range = False, OPT={}):
    '''
    This function plots two variables in a 2D histogram. Outliers are taken into account with the percentile. 
    It plots values below and above the indicated percetiles, but values are not removed from data.
    
    **VARIABLES:**

    - my_run: run(s) we want to check
    - keys: variables we want to plot as histograms. Type: List
    - percentile: percentile used for outliers removal
    - select_range: if we still have many outliers we can select the ranges in x and y axis.
    '''

    # Imports from other libraries
    from .io_functions  import check_key
    from .ana_functions import generate_cut_array, get_units
    from .fig_config    import figure_features, add_grid

    figure_features()
    r_list = my_run["NRun"]
    ch_list = my_run["NChannel"]
    if compare == "CHANNELS": a_list = r_list;  b_list = ch_list 
    if compare == "RUNS":     a_list = ch_list; b_list = r_list
    if compare == "NONE":     a_list = r_list;  b_list = ch_list

    x_data = []; y_data = []
    for run in r_list:
        for ch in ch_list:
            if check_key(my_run[run][ch], "MyCuts") == False:    generate_cut_array(my_run)
            if check_key(my_run[run][ch], "UnitsDict") == False: get_units(my_run)
    figures_list = []
    axes_list = []
    for a in a_list:
        for b in b_list:
            fig, ax = plt.subplots(1,1, figsize = (8,6)); add_grid(ax)

            if compare == "CHANNELS": 
                title = "Run_{} ".format(a);
                label0 = "{}".format(my_run[a][ch_list[0]]["Label"]).replace("#","")
                label1 = "{}".format(my_run[a][ch_list[1]]["Label"]).replace("#","")
                aux_x_data = my_run[a][ch_list[0]][keys[0]][my_run[a][ch_list[0]]["MyCuts"] == True]; aux_y_data = my_run[a][ch_list[1]][keys[1]][my_run[a][ch_list[1]]["MyCuts"] == True]
            if compare == "RUNS":
                title = "Channel_{} ".format(a);
                label0 = "{}".format(my_run[r_list[0]][a]["Label"]).replace("#","")
                label1 = "{}".format(my_run[r_list[1]][a]["Label"]).replace("#","")
                aux_x_data = my_run[r_list[0]][a][keys[0]][my_run[r_list[0]][a]["MyCuts"] == True]; aux_y_data = my_run[r_list[1]][a][keys[1]][my_run[r_list[1]][a]["MyCuts"] == True]
            if compare == "NONE":
                title = "Run_{} Ch_{} - {} vs {} histogram".format(a,b,keys[0],keys[1])
                label0 = ""; label1 = ""
                aux_x_data = my_run[a][b][keys[0]][my_run[a][b]["MyCuts"] == True]; aux_y_data = my_run[a][b][keys[1]][my_run[a][b]["MyCuts"] == True]

            aux_x_data = aux_x_data[~np.isnan(aux_x_data)]; aux_y_data = aux_y_data[~np.isnan(aux_y_data)]
            x_data = aux_x_data; y_data = aux_y_data
            #### Calculate range with percentiles for x-axis ####
            x_ypbot = np.percentile(x_data, percentile[0]); x_yptop = np.percentile(x_data, percentile[1])
            x_ypad = 0.2*(x_yptop - x_ypbot)
            x_ymin = x_ypbot - x_ypad; x_ymax = x_yptop + x_ypad
            #### Calculate range with percentiles for y-axis ####
            y_ypbot = np.percentile(y_data, percentile[0]); y_yptop = np.percentile(y_data, percentile[1])
            y_ypad = 0.2*(y_yptop - y_ypbot)
            y_ymin = y_ypbot - y_ypad; y_ymax = y_yptop + y_ypad

            if "Time" in keys[0]: ax.hist2d(x_data*my_run[run][ch]["Sampling"], y_data, bins=[600,600], range = [[x_ymin*my_run[run][ch]["Sampling"],x_ymax*my_run[run][ch]["Sampling"]],[y_ymin, y_ymax]], density=True, cmap = viridis, norm=LogNorm())
            else:                 ax.hist2d(x_data, y_data, bins=[600,600], range = [[x_ymin,x_ymax],[y_ymin, y_ymax]], density=True, cmap = viridis, norm=LogNorm())
            ax.grid("both")
            fig.supxlabel(label0 + " " + keys[0]+" ("+my_run[run][ch]["UnitsDict"][keys[0]]+")"); fig.supylabel(label1 + " " + keys[1]+" ("+my_run[run][ch]["UnitsDict"][keys[1]]+")")
            fig.suptitle(title)
            if select_range:
                x1 = -1e6
                while x1 == -1e6:
                    try:
                        x1 = float(input("xmin: ")); x2 = float(input("xmax: "))
                        y1 = float(input("ymin: ")); y2 = float(input("ymax: "))
                    except:
                        x1 = -1e6
                ax.hist2d(x_data, y_data, bins=[300,300], range = [[x1,x2],[y1, y2]], density=True, cmap = viridis, norm=LogNorm())
                ax.grid("both")

            figures_list.append(fig)
            axes_list.append(ax)
            if check_key(OPT, "LOGY") == True and OPT["LOGY"] == True: plt.yscale('log'); 
            if check_key(OPT, "SHOW") == True and OPT["SHOW"] == True: 
                plt.ion()
                plt.show()
                while not plt.waitforbuttonpress(-1): pass
                plt.close()
            # else:
            #     plt.close()
            if compare != "NONE": break

    return figures_list, axes_list