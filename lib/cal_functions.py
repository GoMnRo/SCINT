#================================================================================================================================================#
# This library contains function to perform the calibration of our sensors. They are mostly used in the 04Calibration.py macro.                  #
#================================================================================================================================================#

import numpy             as np
import matplotlib.pyplot as plt
import pandas            as pd
from matplotlib.colors import LogNorm
from matplotlib.cm     import viridis
from itertools         import product
# from scipy import stats as st

# Import from other libraries
from .io_functions  import check_key, print_colored, color_list, write_output_file
from .ana_functions import generate_cut_array, get_units
from .fig_config    import figure_features, add_grid
from .fit_functions import gaussian_train_fit, gaussian_train, pmt_spe_fit, gaussian_fit, gaussian
from .vis_functions import vis_var_hist

def vis_persistence(my_run, OPT = {}):
    '''
    \nThis function plot the PERSISTENCE histogram of the given runs&ch.
    \nIt perfoms a cut in 20<"PeakTime"(bins)<50 so that all the events not satisfying the condition are removed. 
    \nBinning is fixed (x=5000, y=1000) [study upgrade].
    \nX_data (time) and Y_data (waveforms) are deleted after the plot to save space.
    \n
    \nWARNING! flattening long arrays leads to MEMORY problems :/
    '''

    figure_features()
    plt.ion()
    for run, ch in product(my_run["NRun"],my_run["NChannel"]):

        generate_cut_array(my_run)
        # cut_min_max(my_run, ["PeakTime"], {"PeakTime":[(st.mode(my_run[run][ch]["PeakTime"])[0]-20)*4e-9, (st.mode(my_run[run][ch]["PeakTime"])[0]+20)*4e-9]})
        # cut_min_max(my_run, ["PeakTime"], {"PeakTime":[4.19e-6, 4.22e-6]})
        # cut_min_max(my_run, ["PeakAmp"], {"PeakAmp":[25,100]})
        # cut_min_max(my_run, ["PedSTD"], {"PedSTD":[-1,4.8]})

        data_flatten = my_run[run][ch]["ADC"][np.where(my_run[run][ch]["MyCuts"] == True)].flatten() ##### Flatten the data array
        time = my_run[run][ch]["Sampling"]*np.arange(len(my_run[run][ch]["ADC"][0])) # Time array
        time_flatten = np.array([time] * int(len(data_flatten)/len(time))).flatten() 

        plt.hist2d(time_flatten,data_flatten,density=True,bins=[5000,1000], cmap = viridis, norm=LogNorm()) 

        plt.colorbar()
        plt.grid(True, alpha = 0.7) # , zorder = 0 for grid behind hist
        plt.title("Run_{} Ch_{} - Persistence".format(run,ch),size = 14)
        plt.xticks(size = 11); plt.yticks(size = 11)
        plt.xlabel("Time (s)", size = 11); plt.ylabel("Counts", size = 11)
        del data_flatten, time, time_flatten
        while not plt.waitforbuttonpress(-1): pass
        plt.clf()
    plt.ioff()
    plt.clf()

def calibrate(my_runs, keys, OPT={}, debug=False):
    '''
    \nComputes calibration hist of a collection of runs. A fit is performed (train of gaussians) and we have as 
    \na return the popt, pcov, perr for the best fitted parameters. Not only that but a plot is displayed.
    \n**VARIABLES:**
    \n- my_run: run(s) we want to check
    \n- keys: variables we want to plot as histograms. Type: List
    \n- OPT: several options that can be True or False. Type: List
      (a) LOGY: True if we want logarithmic y-axis
      (b) SHOW: if True, it will show the calibration plot
    '''

    figure_features()
    for run in my_runs["NRun"]:
        for ch in my_runs["NChannel"]:
            for key in keys:
                if len(my_runs[run][ch].keys()) == 0: 
                    print_colored("\n RUN DOES NOT EXIST. Looking for the next", "WARNING")
                    popt = [-99, -99, -99]; pcov= [-99, -99, -99]; perr = [-99, -99, -99]
                
                else: 
                    det_label = my_runs[run][ch]["Label"]
                    if check_key(my_runs[run][ch], "MyCuts") == False:
                        if debug: print_colored("Cuts not generated. Generating them...", "WARNING")
                        generate_cut_array(my_runs,debug=debug) # If cuts not generated, generate them
                        if debug: print(run, ch, my_runs[run][ch]["MyCuts"])
                    if check_key(my_runs[run][ch], "UnitsDict") == False: get_units(my_runs)          # Get units
                    OPT["SHOW"] == False
                    counts, bins, bars = vis_var_hist(my_runs, [key], OPT=OPT)
                    counts = counts[0]; bins = bins[0]; bars = bars[0]

                    ## New Figure with the fit ##
                    plt.ion(); fig_cal, ax_cal = plt.subplots(1,1, figsize = (8,6)); add_grid(ax_cal)
                    ax_cal.hist(bins[:-1], bins, weights = counts, histtype = "step")
                    fig_cal.suptitle("Run_{} Ch_{} - {} histogram".format(run,ch,key))
                    fig_cal.supxlabel(key+" ("+my_runs[run][ch]["UnitsDict"][key]+")"); fig_cal.supylabel("Counts")

                    #This if could be simplified!!!
                    if det_label != "PMT": #Fit for SiPMs/SC
                        new_params = {}
                        params = {"THRESHOLD": 0.1, "WIDTH": 5, "PROMINENCE": 0.01, "ACCURACY": 1000, "FIT": "gaussian"}
                        for i,param in enumerate(list(params.keys())):
                            if check_key(OPT,param) == True: new_params[param] = OPT[param]
                            else:                            new_params[param] = params[param]

                        x, y, peak_idx, valley_idx, popt, pcov, perr = gaussian_train_fit(counts, bins, bars, new_params, debug=debug)
                        ax_cal.axhline(new_params["THRESHOLD"], ls='--')
                        ax_cal.plot(x[peak_idx], y[peak_idx], 'r.', lw=4)
                        ax_cal.plot(x[valley_idx], y[valley_idx], 'b.', lw=6)
                        ax_cal.plot(x,gaussian_train(x, *popt), label="")

                    else: #Particular calibration fit for PMTs
                        print("Hello, we are working on a funtion to fit PMT spe :)")
                        thresh = int(len(my_runs[run][ch][key])/1e4)
                        x, y, peak_idx, valley_idx, popt, pcov, perr = pmt_spe_fit(counts, bins, bars, thresh)
                        ## Plot threshold, peaks (red) and valleys (blue) ##
                        ax_cal.axhline(thresh, ls='--')
                        ax_cal.plot(x[peak_idx], y[peak_idx], 'r.', lw=4)
                        ax_cal.plot(x[valley_idx], y[valley_idx], 'b.', lw=6)
                        ## Plot the fit ##
                        ax_cal.plot(x,gaussian_train(x, *popt), label="")

                    if check_key(OPT,"LEGEND") == True and OPT["LEGEND"] == True: ax_cal.legend()
                    if check_key(OPT,"LOGY")   == True and OPT["LOGY"]   == True: ax_cal.semilogy(); ax_cal.set_ylim(1)
                    if check_key(OPT,"SHOW")   == True and OPT["SHOW"]   == True:
                        print("SHOW BUT NO TERMINAL FRIEND")

                        if check_key(OPT, "TERMINAL_MODE") == True and OPT["TERMINAL_MODE"] == True:
                            print("TERMINAL FRIEND")
                            plt.ion()
                            plt.show()
                            while not plt.waitforbuttonpress(-1): pass
                            plt.close()

                    try:
                        my_runs[run][ch]["Gain"]         = popt[3]-abs(popt[0])
                        my_runs[run][ch]["MaxChargeSPE"] = popt[3] + abs(popt[5])
                        my_runs[run][ch]["MinChargeSPE"] = popt[3] - abs(popt[5])
                    except IndexError:
                        print_colored("Fit failed to find min of 3 calibration peaks!", "WARNING")
                        my_runs[run][ch]["Gain"]         = -99
                        my_runs[run][ch]["MaxChargeSPE"] = -99
                        my_runs[run][ch]["MinChargeSPE"] = -99

    return popt, pcov, perr

def calibration_txt(run, ch, popt, pcov, filename, info, debug=False):
    '''
    \nComputes calibration parameters for each peak.
    \nGiven popt and pcov which are the output for the best parameters when performing the Gaussian fit.
    \nIt returns an array of arrays: 
    \nsave_calibration = [ [[mu,dmu],[height,dheight],[height,dheight],[sigma,dsigma],
    \n[gain,dgain],[sn0,dsn0],[sn1,dsn1],[sn2,dsn2]], [PEAK 1], [PEAK 2],...]
    \nSave in a txt the calibration parameters to be exported directly.
    \nTakes as input an array of arrays with the computed parameters (see compute_cal_parameters())
    '''

    if all(x !=-99 for x in popt):
        cal_parameters = []
        perr = np.sqrt(np.diag(pcov))    #error for each variable
        fitted_peaks = int(len(popt)/3)  #three parameters fitted for each peak
        for i in np.arange(fitted_peaks): 
            mu     = [popt[(i+0)+2*i], perr[(i+0)+2*i]]  # mu +- dmu
            height = [popt[(i+1)+2*i], perr[(i+1)+2*i]]  # height +- dheight (not saving in txt by default)
            sigma  = [popt[(i+2)+2*i], perr[(i+2)+2*i]]  # sigma +- dsigma
            cal_parameters.append([mu,height,sigma])
            copy_cal = cal_parameters

        for i in np.arange(fitted_peaks): #distances between peaks
            if i == fitted_peaks-1: gain = -99; dgain = -99; sn0 = -99; dsn0 = -99; sn1 = -99; dsn1 = -99; sn2 = -99; dsn2 = -99
            else:
                # GAIN = [mu(i+1) - mu(i)] * 1e-12 /    e-19 (pC)
                gain  = (copy_cal[i+1][0][0]-copy_cal[i][0][0]); dgain = (np.sqrt(copy_cal[i+1][0][1]**2+copy_cal[i][0][1]**2)) #*1e-12/1.602e-19 #when everythong was pC
                
                # SN0 = [mu(i+1)-mu(i)]/sigma(i)
                sn0 = (copy_cal[i+1][0][0]-copy_cal[i][0][0])/copy_cal[i][2][0]
                dsn0 = sn0 * np.sqrt(((copy_cal[i+1][0][1]**2+copy_cal[i][0][1]**2)/((copy_cal[i+1][0][0]-copy_cal[i][0][0])))**2+(copy_cal[i][2][1]/copy_cal[i][2][0])**2)
                
                # SN1 = [mu(i+1)-mu(i)]/sigma(i+1)
                sn1 = (copy_cal[i+1][0][0]-copy_cal[i][0][0])/copy_cal[i+1][2][0]
                dsn1 = sn1 * np.sqrt(((copy_cal[i+1][0][1]**2+copy_cal[i][0][1]**2)/((copy_cal[i+1][0][0]-copy_cal[i][0][0]))**2)+(copy_cal[i+1][2][1]/copy_cal[i+1][2][0])**2)
                
                # SNC = [mu(i+1)-mu(i)]/sqrt(sigma(i)**2+sigma(i+1)**2)
                sn2 = (copy_cal[i+1][0][0]-copy_cal[i][0][0])/(np.sqrt(copy_cal[i][2][0]**2+copy_cal[i+1][2][0]**2))
                dsn2 = sn2 * np.sqrt((dgain/gain)**2+((copy_cal[i][2][0]*copy_cal[i][2][1])/((copy_cal[i][2][0])**2+(copy_cal[i+1][2][0])**2))**2+((copy_cal[i+1][2][0]*copy_cal[i+1][2][1])/((copy_cal[i][2][0])**2+(copy_cal[i+1][2][0])**2))**2)

            cal_parameters[i].append([gain, dgain]); 
            cal_parameters[i].append([sn0, dsn0]);cal_parameters[i].append([sn1, dsn1]);cal_parameters[i].append([sn2, dsn2])

        fitted_peaks = len(cal_parameters)
        for i in np.arange(fitted_peaks): #three parameters fitted for each peak
                    print("\nPeak:", i)
                    print("MU     +- DMU:\t  ",['{:.2E}'.format(item) for item in cal_parameters[i][0]])
                    print("HEIGHT +- DHEIGHT:",['{:.2E}'.format(item) for item in cal_parameters[i][1]])
                    print("SIGMA  +- DSIGMA: ",['{:.2E}'.format(item) for item in cal_parameters[i][2]])
                    print("GAIN   +- DGAIN:  ",['{:.2E}'.format(item) for item in cal_parameters[i][3]])
                    print("SN0    +- DSN0:\t  ",['{:.2E}'.format(item) for item in cal_parameters[i][4]])
                    print("SN1    +- DSN1:\t  ",['{:.2E}'.format(item) for item in cal_parameters[i][5]])
                    print("SN2    +- DSN2:\t  ",['{:.2E}'.format(item) for item in cal_parameters[i][6]])
        
        write_output_file(run, ch, cal_parameters, filename, info, header_list=["RUN","OV","PEAK","MU","DMU","SIG","DSIG","\t","GAIN","DGAIN","SN0","DSN0","SN1","DSN1","SN2","DSN2"], extra_tab=[3])

def get_gains(run,channels,folder_path="TUTORIAL",debug=False):
    gains = dict.fromkeys(channels) ; Dgain = dict.fromkeys(channels)
    for c, ch in enumerate(channels):
        my_table = pd.read_csv("../fit_data/"+folder_path+"/Anagain_ch%i.txt"%ch, header=None,sep = "\t",usecols=np.arange(16),names=["RUN","OV","PEAK","MU","DMU","SIG","DSIG","\t","GAIN","DGAIN","SN0","DSN0","SN1","DSN1","SN2","DSN2"])
        my_table = my_table.iloc[1:]
        gains[ch] = list(np.array(my_table["GAIN" ]).astype(float)[my_table["RUN"]==str(run)])
        Dgain[ch] = list(np.array(my_table["DGAIN"]).astype(float)[my_table["RUN"]==str(run)])
        if debug: print("\nGAIN TXT FOR CHANNEL %i"%ch ); display(my_table)
    
    return gains, Dgain

def scintillation_txt(run, ch, popt, pcov, filename, info):
    '''
    \nComputes charge parameters.
    \nGiven popt and pcov which are the output for the best parameters when performing the Gaussian fit.
    \nIt returns an array of arrays: 
    \nsave_scintillation = [ [[mu,dmu],[height,dheight],[sigma,dsigma],] ]
    \nSave in a txt the calibration parameters to be exported directly.
    \nTakes as input an array of arrays with the computed parameters (see compute_charge_parameters())
    '''

    charge_parameters = []
    perr0 = np.sqrt(np.diag(pcov))  #error for each variable
    # perr1 = np.sqrt(np.diag(pcov[1]))  #error for each variable

    mu       = [popt[1], perr0[1]]  # mu +- dmu
    height   = [popt[0], perr0[0]]  # height +- dheight (not saving in txt by default)
    sigma    = [abs(popt[2]), perr0[2]]  # sigma +- dsigma
    charge_parameters.append([mu,height,sigma])
    
    print(len(charge_parameters))
    print(charge_parameters)

    print("MU +- DMU:",               ['{:.2f}'.format(item) for item in charge_parameters[0][0]])
    print("HEIGHT +- DHEIGHT:",       ['{:.2f}'.format(item) for item in charge_parameters[0][1]])
    print("SIGMA +- DSIGMA:",         ['{:.2f}'.format(item) for item in charge_parameters[0][2]])
    
    write_output_file(run, ch, charge_parameters, filename, info, header_list=["RUN","MU","DMU","SIG","DSIG"])


def charge_fit(my_runs, keys, OPT={}):
    '''
    \nComputes charge hist of a collection of runs. A fit is performed (1 gaussian) and we have as 
    \na return the popt, pcov, perr for the best fitted parameters. Not only that but a plot is displayed.
    \n**VARIABLES:**
    \n- my_run: run(s) we want to check
    \n- keys: variables we want to plot as histograms. Type: List
    \n- OPT: several options that can be True or False. Type: List
      (a) LOGY: True if we want logarithmic y-axis
      (b) SHOW: if True, it will show the calibration plot
    '''

    next_plot = False
    counter = 0
    all_counts, all_bins, all_bars = vis_var_hist(my_runs, keys, OPT=OPT)
    all_popt=[]; all_pcov=[]; all_perr=[]
    for run, ch, key in product(my_runs["NRun"], my_runs["NChannel"], keys):        
        
        if check_key(my_runs[run][ch], "MyCuts") == False:    generate_cut_array(my_runs) #if no cuts, generate them
        if check_key(my_runs[run][ch], "UnitsDict") == False: get_units(my_runs)          #if no units, generate them
        # try:
        thresh = int(len(my_runs[run][ch][key])/1000)

        ## New Figure with the fit ##
        plt.ion()
        fig_ch, ax_ch = plt.subplots(1,1, figsize = (8,6))
        add_grid(ax_ch)
        counts = all_counts[counter]; bins = all_bins[counter]; bars = all_bars[counter]
        ax_ch.hist(bins[:-1], bins, weights = counts, histtype="step")
        fig_ch.suptitle("Run_{} Ch_{} - {} histogram".format(run,ch,key)); fig_ch.supxlabel(key+" ("+my_runs[run][ch]["UnitsDict"][key]+")"); fig_ch.supylabel("Counts")
        
        ### --- 1x GAUSSIAN FIT --- ###
        x, popt, pcov, perr = gaussian_fit(counts, bins, bars,thresh,fit_function="gaussian")
        print("Chi2/N?: ", (sum((my_runs[run][ch][key]-gaussian(my_runs[run][ch]["Sampling"]*np.arange(len(my_runs[run][ch][key])), *popt))**2))/len(my_runs[run][ch][key]))
        ax_ch.plot(x,gaussian(x, *popt), label="")

        if check_key(OPT,"LEGEND") == True and OPT["LEGEND"] == True:
            ax_ch.legend()
        if check_key(OPT,"LOGY") == True and OPT["LOGY"] == True:
            ax_ch.semilogy()
            plt.ylim(ymin=1, ymax=1.2*max(counts))

        ## Repeat customized fit ##
        confirmation = input(color_list("magenta")+"Are you happy with the fit? (y/n) "+color_list("end"))
        if "n" in confirmation:
            print("\n--- Repeating the fit with input parameters (\u03BC \u00B1 \u03C3) \u03B5 [{:0.2f}, {:0.2f}] ---".format(x[0],x[-1]))
            mean  = input(color_list("magenta")+"Introduce MEAN value for the fit: " +color_list("end"))
            sigma = input(color_list("magenta")+"Introduce SIGMA value for the fit: "+color_list("end"))

            x, popt, pcov, perr = gaussian_fit(counts, bins, bars,thresh,custom_fit=[float(mean),float(sigma)])
            ax_ch.plot(x, gaussian(x, *popt), label="")
            all_popt.append(popt); all_pcov.append(pcov); all_perr.append(perr)
        else:
            all_popt.append(popt); all_pcov.append(pcov); all_perr.append(perr)
            plt.close()
            continue
        
        if check_key(OPT,"SHOW") == True and OPT["SHOW"] == True:
            while not plt.waitforbuttonpress(-1): pass
        counter += 1
        plt.close()
        # except KeyError:
        #     print("Empty dictionary. No computed charge.")
    
    return all_popt, all_pcov, all_perr