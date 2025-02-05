# helper functions for processing results
import pickle 
import numpy as np

def generate_pickle_object(log_files_folder):
    pkl_file = log_files_folder + "raw_result.pkl"
    with open(pkl_file, "rb") as f:
            trial_result_obj = pickle.load(f)
    return trial_result_obj

def get_patch(log_files_folder):
    patch_file = log_files_folder + "experiment.patch"
    try:
        with open(patch_file, "r") as f:
            patch = f.read()
        return patch
    except FileNotFoundError: # No patches found (i.e. variants with improved fitness)
        return None

def get_num_unique_variants_evaluated(pkl_obj):
    cache_info = pkl_obj['cache_info']
    return cache_info['currsize']

def get_num_variants_evaluated(pkl_obj):
    run_results = pkl_obj['run_results']
    return len(run_results)

def get_num_successful_variants_evaluated(pkl_obj):
    run_results = pkl_obj['run_results']
    num_success = 0
    for result in run_results:
        if result['status'] == 'SUCCESS':
            num_success += 1
    return num_success

def num_iterations_till_patch_found(df):
    pkl_obj, patch = df['pkl_obj'], df['patch']
    run_results = pkl_obj['run_results']
    for i, result in enumerate(run_results):
        patch = patch.replace('\n', '')
        if str(result['patch']) == str(patch):
            return i
    return -1 # Patch not found

def get_unique_statuses(pkl_obj):
    run_results = pkl_obj['run_results']
    unique_statuses = set()
    for result in run_results:
        unique_statuses.add(result['status'])
    return unique_statuses

def get_status_cum_count(pkl_obj, status_name):
    run_results = pkl_obj['run_results']
    has_status_code = []
    for result in run_results:
        if result['status'] == status_name:
            has_status_code.append(1)
        else:
            has_status_code.append(0)
    return np.cumsum(has_status_code)

def get_run_times(pkl_obj):
    run_results = pkl_obj['run_results']
    run_times = []
    for result in run_results:
        if result['status'] == 'SUCCESS':
            run_times.append(result['fitness'])
    return np.array(run_times)

def get_average_vs_time(array):
    return np.cumsum(array) / np.arange(1, len(array) + 1)