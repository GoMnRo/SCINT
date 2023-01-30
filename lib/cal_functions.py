import numpy as np
# import copy
# import sys

import scipy
from scipy.signal import find_peaks
from scipy.optimize import curve_fit

import matplotlib.pyplot as plt

from itertools import product
from .io_functions import check_key,print_keys
from .vis_functions import vis_var_hist
from .fit_functions import gaussian,gaussian_train, loggaussian, loggaussian_train

from .fig_config import (
    add_grid,
    figure_features)  # <--- import customized functions

def calibrate(my_runs, keys, OPT={}):
    """Computes calibration hist of a collection of runs and returns gain and SPE charge limits"""
    
    plt.ion()
    next_plot = False
    idx = 0
    for run, ch, key in product(my_runs["NRun"], my_runs["NChannel"], keys):
        try:
            idx = idx + 1

            # Threshold value (for height of peaks and valleys)
            thresh = int(len(my_runs[run][ch][key])/1000)
            wdth = 10
            prom = 0.5
            acc  = 1000

            # my_run = copy_single_run(my_runs, [run], [ch], [key])
            counts, bins, bars = vis_var_hist(my_runs, [key], OPT=OPT)

            fig, ax = plt.subplots(1,1, figsize = (8,6))
            add_grid(ax)
            counts = counts[0]; bins = bins[0]; bars = bars[0]
            ax.hist(bins[:-1], bins, weights = counts)
            fig.supxlabel(key+" ("+my_runs[run][ch]["Units"][key]+")"); fig.supylabel("Counts")

            # Create linear interpolation between bins to search peaks in these variables
            x = np.linspace(bins[1],bins[-2],acc)
            y_intrp = scipy.interpolate.interp1d(bins[:-1],counts)
            y = y_intrp(x)
            # plt.plot(x,y)

            # Find indices of peaks
            # peak_idx, _ = find_peaks(np.log10(y), height = np.log10(thresh), width = wdth, prominence = prom)
            peak_idx, _ = find_peaks(y, height = thresh, width = wdth, prominence = prom)

            # Find indices of valleys (from inverting the signal)
            # valley_idx, _ = find_peaks(-np.log10(y), height = [-np.max(np.log10(counts)), -np.log10(thresh)], width = wdth, prominence = prom)
            valley_idx, _ = find_peaks(-y, height = [-np.max(counts), -thresh], width = wdth)
            
            # Plot threshold, peaks (red) and valleys (blue)
            ax.axhline(thresh, ls='--')
            ax.plot(x[peak_idx], y[peak_idx], 'r.', lw=4)
            ax.plot(x[valley_idx], y[valley_idx], 'b.', lw=6)

            height,center,width = [],[],[]
            initial = []
            
            n_peaks = 6
            if len(peak_idx)-1 < n_peaks:
                n_peaks = len(peak_idx)-1
            
            for i in range(n_peaks):
                x_space = np.linspace(x[peak_idx[i]],x[peak_idx[i+1]],acc)
                step    = x_space[1]-x_space[0]
                x_gauss = x_space-int(acc/2)*step
                x_gauss = x_gauss[x_gauss >= bins[0]]
                y_gauss = y_intrp(x_gauss)
                # plt.plot(x_gauss,y_gauss,ls="--",alpha=0.9)

                try:
                    # popt, pcov = curve_fit(loggaussian,x_gauss,np.log10(y_gauss),p0=[np.log10(y[peak_idx[i]]),x[peak_idx[i]],abs(wdth*(bins[0]-bins[1]))])
                    popt, pcov = curve_fit(gaussian,x_gauss,y_gauss,p0=[y[peak_idx[i]],x[peak_idx[i]],abs(wdth*(bins[0]-bins[1]))])
                    # height.append(popt[0])
                    # center.append(popt[1])
                    # width.append(popt[2])
                    initial.append(popt[1])
                    initial.append(popt[0])
                    initial.append(popt[2])
                    ax.plot(x_gauss,gaussian(x_gauss, *popt), ls = "--", c = "black", alpha = 0.5)
                
                except:
                    initial.append(x[peak_idx[i]])
                    initial.append(y[peak_idx[i]])
                    initial.append(abs(wdth*(bins[0]-bins[1])))
                    print("Peak %i could not be fitted"%i)

            try:
                # popt, pcov = curve_fit(loggaussian_train,x[:peak_idx[-1]],np.log10(y[:peak_idx[-1]]),p0=initial)
                popt, pcov = curve_fit(gaussian_train,x[:peak_idx[-1]], y[:peak_idx[-1]], p0=initial)
            except:
                popt = initial
                print("Full fit could not be performed")
            ax.plot(x[:peak_idx[-1]],gaussian_train(x[:peak_idx[-1]], *popt), label="")
            # plt.legend()
            if check_key(OPT,"LOGY") == True and OPT["LOGY"] == True:
                ax.semilogy()
            
            # plt.ylim(thresh*0.9,np.max(counts)*1.1)
            # plt.xlim(x[peak_idx[0]]-abs(wdth*(bins[0]-bins[1])),x[peak_idx[-1]]*1.1)
            
            while not plt.waitforbuttonpress(-1): pass

            plt.clf()
            if check_key(OPT,"PRINT_KEYS") == True and OPT["PRINT_KEYS"] == True:
                return print_keys(my_runs)

            my_runs[run][ch]["Gain"] = popt[3]-abs(popt[0])
            my_runs[run][ch]["MaxChargeSPE"] = popt[3] + abs(popt[5])
            print("SPE gauss parameters %.2E, %.2E, %.2E"%(popt[3],popt[4],popt[5]))
            # print("SPE max charge for run %i ch %i = %.2E"%(run,ch,popt[3] + abs(popt[5])))
            my_runs[run][ch]["MinChargeSPE"] = popt[3] - abs(popt[5])
            # print("SPE min charge for run %i ch %i = %.2E"%(run,ch,popt[3] - abs(popt[5])))
        except KeyError:
            return print("Empty dictionary. No calibration to show.")
    plt.ioff()
    plt.clf()
