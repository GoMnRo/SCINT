import sys, copy
import numpy as np
import matplotlib.pyplot as plt
from scipy     import stats as st
from itertools import product
import numba

from .io_functions import check_key, print_keys, print_colored

def insert_variable(my_runs, var, key, debug = False):
    '''
    Insert values for each type of signal
    '''

    for run,ch in product(np.array(my_runs["NRun"]).astype(int),np.array(my_runs["NChannel"]).astype(int)):
        i = np.where(np.array(my_runs["NRun"]).astype(int) == run)[0][0]
        j = np.where(np.array(my_runs["NChannel"]).astype(int) == ch)[0][0]

        try:
            my_runs[run][ch][key] = var[j]
        except KeyError: 
            if debug: print_colored("Inserting value...", "DEBUG")

def generate_cut_array(my_runs,debug=False):
    '''
    This function generates an array of bool = True with length = NEvts. If cuts are applied and then you run this function, it resets the cuts.
    '''

    for run, ch in product(my_runs["NRun"], my_runs["NChannel"]):    
        if debug: print_colored("Keys in my_run before generating cut array: " +str(my_runs[run][ch].keys()), "DEBUG")
        for key in my_runs[run][ch].keys():
            # if debug: print("Output of find function for key: ",key,key.find("ADC"))
            # if key.find("ADC") == 0:
            if "ADC" in key:      ADC_key = key
            elif "Charge" in key: ADC_key = key
            elif "Peak" in key:   ADC_key = key
        my_runs[run][ch]["MyCuts"] = np.ones(len(my_runs[run][ch][ADC_key]),dtype=bool)
        if debug: print_colored("Keys in my_run after generating cut array: "+str(my_runs[run][ch].keys()), "DEBUG")

def compute_peak_variables(my_runs, key = "ADC", label = "", debug = False):
    '''
    Computes the peaktime and amplitude of a collection of a run's collection in standard format
    '''

    for run,ch in product(my_runs["NRun"],my_runs["NChannel"]):
        try:
            my_runs[run][ch][label+"PeakAmp" ] = np.max    (my_runs[run][ch][key][:,:]*my_runs[run][ch][label+"PChannel"],axis=1)
            my_runs[run][ch][label+"PeakTime"] = np.argmax (my_runs[run][ch][key][:,:]*my_runs[run][ch][label+"PChannel"],axis=1)
            print_colored("Peak variables have been computed for run %i ch %i"%(run,ch), "blue")
        except KeyError: 
            if debug: print_colored("*EXCEPTION: for %i, %i, %s peak variables could not be computed"%(run,ch,key), "WARNING")

def compute_pedestal_variables(my_runs, key = "ADC", label = "", buffer = 200, debug = False):
    '''
    Computes the pedestal variables of a collection of a run's collection in standard format
    '''

    for run,ch in product(my_runs["NRun"],my_runs["NChannel"]):
        try:
            # ped_lim = st.mode(my_runs[run][ch][label+"PeakTime"], keepdims=True)[0][0]-buffer # Deprecated function
            values,counts = np.unique(my_runs[run][ch][label+"PeakTime"], return_counts=True)
            ped_lim = values[np.argmax(counts)]-buffer
            if ped_lim < 0: ped_lim = 200
            my_runs[run][ch][label+"PedSTD"]  = np.std (my_runs[run][ch][key][:,:ped_lim],axis=1)
            my_runs[run][ch][label+"PedMean"] = np.mean(my_runs[run][ch][key][:,:ped_lim],axis=1)
            my_runs[run][ch][label+"PedMax"]  = np.max (my_runs[run][ch][key][:,:ped_lim],axis=1)
            my_runs[run][ch][label+"PedMin"]  = np.min (my_runs[run][ch][key][:,:ped_lim],axis=1)
            my_runs[run][ch][label+"PedLim"]  = ped_lim
            # my_runs[run][ch][label+"PedRMS"]  = np.sqrt(np.mean(np.abs(my_runs[run][ch][key][:,:ped_lim]**2),axis=1))
            print("Pedestal variables have been computed for run %i ch %i"%(run,ch))
        except: 
            KeyError
            if debug: print("*EXCEPTION: for ",run,ch,key," pedestal variables could not be computed")
def compute_pedestal_variables_sliding_window(my_runs, key = "ADC", label = "", ped_lim = 400,sliding=50,pretrigger=800, start = 0, debug = False):
    """Computes the pedestal variables of a collection of a run's collection in standard format"""
    for run,ch in product(my_runs["NRun"],my_runs["NChannel"]):
        try:
            ADCs_aux=my_runs[run][ch][key]
            ADCs_s=compute_pedestal_sliding_windows(ADCs_aux,ped_lim=ped_lim,sliding=sliding,pretrigger=pretrigger)
            
            my_runs[run][ch][label+"PedSTD"]  = np.std (ADCs_s[:,start:(start+ped_lim)],axis=1)
            my_runs[run][ch][label+"PedMean"] = np.mean(ADCs_s[:,start:(start+ped_lim)],axis=1)
            my_runs[run][ch][label+"PedMax"]  = np.max (ADCs_s[:,start:(start+ped_lim)],axis=1)
            my_runs[run][ch][label+"PedMin"]  = np.min (ADCs_s[:,start:(start+ped_lim)],axis=1)
            my_runs[run][ch][label+"PedLim"]  = ped_lim
            # my_runs[run][ch][label+"PedRMS"]  = np.sqrt(np.mean(np.abs(ADCs_s[:,start:(start+ped_lim)]**2),axis=1))
            print("Pedestal variables have been computed for run %i ch %i"%(run,ch))
        except: 
            KeyError
            if debug: print("*EXCEPTION: for ",run,ch,key," pedestal variables could not be computed")

def compute_ana_wvfs(my_runs, debug = False):
    '''
    Computes the peaktime and amplitude of a collection of a run's collection in standard format
    '''

    for run,ch in product(np.array(my_runs["NRun"]).astype(int),np.array(my_runs["NChannel"]).astype(int)):

        my_runs[run][ch]["ADC"] = my_runs[run][ch]["RawPChannel"]*((my_runs[run][ch]["RawADC"].T-my_runs[run][ch]["RawPedMean"]).T)
        print_colored("Analysis wvfs have been computed for run %i ch %i"%(run,ch), "blue")
        if debug: print_keys(my_runs)

        del my_runs[run][ch]["RawADC"] # After ADC is computed, delete RawADC from memory

def get_units(my_runs, debug = False):
    '''
    Computes and store in a dictionary the units of each variable.  
    '''
    
    for run, ch in product(np.array(my_runs["NRun"]).astype(int),np.array(my_runs["NChannel"]).astype(int)):
        keys = my_runs[run][ch].keys()
        aux_dic = {}
        for key in keys:
            if "Amp" in key or "Ped" in key or "ADC" in key: aux_dic[key] = "ADC"
            elif "Time" in key or "Sampling" in key:         aux_dic[key] = "s"
            elif "Charge" in key:                            aux_dic[key] = "pC"
            else:                                            aux_dic[key] = "a.u."
            
        my_runs[run][ch]["UnitsDict"] = aux_dic

def compute_power_spec(ADC, timebin, debug = False):
    aux = [] 
    aux_X = np.fft.rfftfreq(len(ADC[0]), timebin)
    for i in range(len(ADC)):
        aux.append(np.fft.rfft(ADC[i]))
    return np.absolute(np.mean(aux, axis = 0)), np.absolute(aux_X)

def compute_pedestal_sliding_windows(ADC,ped_lim=400,sliding=50,pretrigger=800, start = 0):
    """Taking the best between different windows in pretrigger"""
    pedestal_vars=dict();
    slides=int((pretrigger-ped_lim)/sliding);
    N_wvfs=ADC.shape[0];
    aux=np.zeros((N_wvfs,slides))
    for i in range(slides):
        aux[:,i]=np.std (ADC[:,(i*sliding+start):(i*sliding+ped_lim+start)],axis=1)
    #put first in the wvf the appropiate window, the one with less std:
    shifts= np.argmin (aux,axis=1)*(-1)*sliding
    ADC_s = shift_ADCs(ADC,shifts)
    #compute all ped variables, now with the best window available

    return ADC_s

@numba.njit
def shift_ADCs(ADC,shift):
        N_wvfs=ADC.shape[0]
        aux_ADC=np.zeros(ADC.shape)
        for i in range(N_wvfs):
            aux_ADC[i]=shift4_numba(ADC[i],int(shift[i])) # Shift the wvfs
        return aux_ADC

# eficient shifter (c/fortran compiled); https://stackoverflow.com/questions/30399534/shift-elements-in-a-numpy-array
@numba.njit
def shift4_numba(arr, num, fill_value=0):#default shifted value is 0, remember to always substract your pedestal first
    if   num > 0:
        return np.concatenate((np.full(num, fill_value), arr[:-num]))
    elif num < 0:
        return np.concatenate((arr[-num:], np.full(-num, fill_value)))
    else:#no shift
        return arr


