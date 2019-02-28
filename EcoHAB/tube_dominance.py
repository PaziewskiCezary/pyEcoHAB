from __future__ import print_function, division
import EcoHab
from ExperimentConfigFile import ExperimentConfigFile
from data_info import *
import os
import utility_functions as utils
import numpy as np
import matplotlib.pyplot as plt
from write_to_file import save_single_histograms, write_csv_rasters, write_csv_tables, write_csv_alone
from plotfunctions import single_in_cohort_soc_plot, make_RasterPlot, single_heat_map
from numba import jit
from collections import OrderedDict
nbins = 10
homepath = os.path.expanduser("~/")

pipe_opposite_antenna = { 1:2,
                          2:1,
                          3:4,
                          4:3,
                          5:6,
                          6:5,
                          7:8,
                          8:7}
cage_opposite_antenna = {1:8,
                         2:3,
                         3:2,
                         4:5,
                         5:4,
                         6:7,
                         7:6,
                         8:1}


def get_states_and_readouts(antennas, times, t1, t2):
    before = utils.get_idx_pre(t1, times)
    between = utils.get_idx_between(t1, t2, times)
    after = utils.get_idx_post(t2, times)
    states = []
    readouts = []
    if before is not None:
        states.append(antennas[before])
        readouts.append(times[before])
    for idx in between:
        states.append(antennas[idx])
        readouts.append(times[idx])
    if after is not None:
        states.append(antennas[after])
        readouts.append(times[after])
    assert(len(states) == len(readouts))
    return states, readouts


def mice_in_different_spots(states1, states2):
    for s1 in states1:
        if s1 in states2:
            return False
    return True


def get_times_antennas(ehd, mouse, t_1, t_2):
    ehd.mask_data(t_1, t_2)
    antennas, times = ehd.getantennas(mouse), ehd.gettimes(mouse)
    ehd.unmask_data()
    return times, antennas


def get_more_states(antennas, times, idx, next_idx, last_states, last_readouts):
    states = last_states[:]
    readouts = last_readouts[:]
    m_change_antenna = utils.change_state(antennas)
    while True:
        next_m1idx = m_change_antenna[next_idx]
        new_antenna = antennas[next_m1idx]
        states.append(new_antenna)
        readouts.append(times[next_m1idx])
        if new_antenna not in states[:-1]:
            break
        idx, next_idx = idx + 1, next_idx + 1
    return states, readouts, idx, next_idx


def check_mouse1_pushing_out_mouse2(antennas1, times1, antennas2, times2):
    m1_change_antenna = utils.change_state(antennas1)
    idx, next_idx = 0, 1
    while idx < len(m1_change_antenna) - 2:
        m1idx, next_m1idx = m1_change_antenna[idx], m1_change_antenna[next_idx]
        m1_states = [antennas1[m1idx], antennas1[next_m1idx]]
        m1_readouts = [times1[m1idx], times1[next_m1idx]]
        idx, next_idx = idx + 1, next_idx + 1
        if utils.in_chamber(*m1_states):
            continue
        #add states until you get something else than the two first antennas
        m1_states, m1_readouts, idx, next_idx = get_more_states(antennas1,
                                                                times1,
                                                                idx,
                                                                next_idx,
                                                                m1_states,
                                                                m1_readouts)
        if len(utils.get_idx_between(m1_readouts[0], m1_readouts[-1], times2)) == 0:
            continue
        m2_states, m2_readouts = get_states_and_readouts(antennas2, times2,
                                                            m1_readouts[0], m1_readouts[-1])
        if mice_in_different_spots(m1_states, m2_states): # mice in different parts of the system
            continue
        if pipe_opposite_antenna[m1_states[0]] not in m2_states: # mouse does not start near opposite antenna
            continue
        if m1_states[0] in m2_states[:2]: # mice start at the same antenna (following not tube dominance)
            continue
        next_m1idx = m1_change_antenna[next_idx]
        m1_full_state = antennas1[m1idx:next_m1idx+1]
        m1_full_readouts = times1[m1idx:next_m1idx+1]
        print('mouse 1')
        print(m1_full_state, m1_full_readouts)
        print('mouse 2')
        print(m2_states, m2_readouts)
    

def tube_dominance_2_mice_single_phase(ehd, mouse1, mouse2, t_start, t_end):
    """We're checking here, how many times mouse1 dominates over mouse2
    between t_start and t_end.

    """
    domination_counter = 0
      
    m1_times, m1_antennas = get_times_antennas(ehd, mouse1, t_start, t_end)
    m2_times, m2_antennas = get_times_antennas(ehd, mouse2, t_start, t_end)
    check_mouse1_pushing_out_mouse2(m1_antennas, m1_times, m2_antennas, m2_times)
        
    return domination_counter

def check_mice(t1_m1, t2_m1, a1_m1, a2_m1, mouse2_antennas, mouse2_times):
    #print('mouse 1', t1_m1, a1_m1, t2_m1, a2_m1)
   
    
    m2_before = get_idx_pre(t1_m1, mouse2_times)
    m2_idxs = get_idx_between(t1_m1, t2_m1, mouse2_times)
    m2_after = get_idx_post(t2_m1, mouse2_times)

    m2_states = []
    m2_times = []
    if m2_before:
        m2_states.append(mouse2_antennas[m2_before])
        m2_times.append(mouse2_times[m2_before])
    for idx in m2_idxs:
        m2_states.append(mouse2_antennas[idx])
        m2_times.append(mouse2_times[idx])
    if m2_after:
        m2_states.append(mouse2_antennas[m2_after])
        m2_times.append(mouse2_times[m2_after])
    for i, t in enumerate(m2_times):
        print('mouse2', t, m2_states[i],)

               
def tube_dominance_2_mice_single_phase_alternative(ehd, mouse1, mouse2, t_start, t_end):
    """We're checking here, how many times mouse1 dominates over mouse2
    between t_start and t_end.
    """
    domination_counter = 0
    ehd.mask_data(t_start, t_end)
    antennas1 = ehd.getantennas(mouse1)
    times1 = ehd.gettimes(mouse1)
    antennas2 = ehd.getantennas(mouse2)
    times2 = ehd.gettimes(mouse2)
   
    pre = 0
    for idx in change_idx:
        t1m1 = times1[pre]
        t2m1 = times1[idx+1]
        a1m1 = antennas1[pre]
        a1m2 = antennas1[idx+1]
        
    

def tube_domination_single_phase(ehd, cf, phase, print_out=True):
    mice = ehd.mice
    st, en = cf.gettime(phase)
    domination =  np.zeros((len(mice), len(mice)))
    if print_out:
        print(phase)
    for i, mouse1 in enumerate(mice):
        for j, mouse2 in enumerate(mice):
            if i != j:
                domination[i, j] = tube_dominance_2_mice_single_phase(ehd,
                                                                      mouse1,
                                                                      mouse2,
                                                                      st,
                                                                      en)
    return domination


def tube_domination_whole_experiment(ehd, cf, main_directory, prefix, remove_mouse=None, print_out=True):
    phases = cf.sections()
    phases = utils.filter_dark(phases)
    mice = ehd.mice
    add_info_mice = utils.add_info_mice_filename(remove_mouse)
    domination = np.zeros((len(phases), len(mice), len(mice)))
    fname_ = 'tube_domination_%s%s.csv' % (prefix, add_info_mice)
    for i, phase in enumerate(phases):
        domination[i] = tube_domination_single_phase(ehd, cf, phase, print_out=print_out)
        save_single_histograms(domination[i],
                               'tube_dominance_alternative',
                               mice,
                               phase,
                               main_directory,
                               'tube_dominance_alternative/histograms',
                               prefix,
                               additional_info=add_info_mice)
        single_heat_map(domination[i],
                        'tube_dominance_alternative',
                        main_directory,
                        mice,
                        prefix,
                        phase,
                        xlabel='domineering mouse',
                        ylabel='pushed out mouse',
                        subdirectory='tube_dominance_alternative/histograms',
                        vmax=None,
                        vmin=None,
                        xticks=mice,
                        yticks=mice)
    write_csv_rasters(mice,
                      phases,
                      domination,
                      main_directory,
                      'tube_dominance_alternative/raster_plots',
                      fname_)
    make_RasterPlot(main_directory,
                    'tube_dominance_alternative/raster_plots',
                    domination,
                    phases,
                    fname_,
                    mice,
                    title='# dominations')
    
if __name__ == '__main__':
    for new_path in datasets:
        path = os.path.join(homepath, new_path)
        prefix = utils.make_prefix(path)
        if new_path in remove_tags:
            remove_mouse = remove_tags[new_path]
        else:
            remove_mouse = None
        if new_path not in antenna_positions:
            antenna_positions[new_path] = None
        if new_path not in how_many_appearances:
            how_many_appearances[new_path] = 500
        if remove_mouse:
            ehd = EcoHab.EcoHabData(path=path,
                                    _ant_pos=antenna_positions[new_path],
                                    remove_mice=remove_mouse,
                                    how_many_appearances=how_many_appearances[new_path])
        else:
            ehd = EcoHab.EcoHabData(path=path,
                                    _ant_pos=antenna_positions[new_path],
                                    how_many_appearances=how_many_appearances[new_path])

        prefix = utils.make_prefix(path)
        res_dir = utils.results_path(path)
        cf = ExperimentConfigFile(path)
        tube_domination_whole_experiment(ehd, cf, res_dir, prefix, remove_mouse=None, print_out=True)
