import random
import json
import subprocess
import configparser
import math
from pathlib import Path
import os
import copy
from tqdm import tqdm

def seed(seed):
    random.seed(seed)

def make_abs_path(bins):
    # Use absolute paths for test cases & SAT/UNSAT label
    root_dir = os.getcwd()
    in_path = root_dir + "/examples/code/benchmark"
    for bin in bins:
        for i, elem in enumerate(bin):
            test_case_type = 'SAT' if elem.split('/')[-1].count('u') == 1 else 'UNSAT'
            bin[i] = f"{in_path}/{elem} {test_case_type}"

def cross_val_setup(args, train_set_size=20, num_replications=5):
    # Generate the folds
    with open('examples/code/benchmark/sat_uniform.json', 'r') as file:
        bins = json.load(file)

    # Make absolute paths
    make_abs_path(bins)
    
    # Split into train test
    train_sets = [None for _ in range(num_replications)]
    
    assert train_set_size % len(bins) == 0, "There must be equal distribution of each test case type in train_set"

    # Load the training sets
    with open("experiments/generate_coverage/max_coverage_test_suites.json", 'r') as file:
        possible_train_sets = json.load(file)

    for i in range(num_replications):
        train_sets[i] = copy.deepcopy(possible_train_sets[str(i)])
        make_abs_path(train_sets[i])

    # Generate the replications
    replications = {}
    for replication_num in range(num_replications):
        replications[replication_num] = {"train_test_cases": train_sets[replication_num]}
    
    cross_validation_setup = {}
    cross_validation_setup['train_set_size'] = train_set_size
    cross_validation_setup['num_replications'] = num_replications
    cross_validation_setup['replications'] = replications
    cross_validation_setup['all_test_cases'] = bins

    os.makedirs(args.results_dir, exist_ok=True)
    with open(f'{args.results_dir}/cross_val_setup.json', 'w') as file:
        json.dump(cross_validation_setup, file, indent=4)
    
    return cross_validation_setup

def set_operator_selector_config(config, operator_selector):
    config["search"]["operator_selector"] = operator_selector
    if operator_selector == 'UniformSelector':
        pass # No additional config required
    elif operator_selector == 'WeightedSelector':
        initial_weights = [1]*8 + [0]*4 # No delete operators
        config["search"]["initial_weights"] = '\n' + '\n'.join([str(weight) for weight in initial_weights])
    elif operator_selector == 'EpsilonGreedy':
        config["search"]["epsilon"] = "0.2"
    elif operator_selector == 'ProbabilityMatching':
        num_operators = len(config["search"]["possible_edits"].split('\n')) - 1
        config["search"]["p_min"] = f"{1/(2 * num_operators)}"
    elif operator_selector == 'UCB':
        config["search"]["c"] = f"{math.sqrt(2)}" # COMP0089: c=root(2) is used in the lectures for log expected regret
    elif operator_selector == 'PolicyGradient':
        config["search"]["alpha"] = "0.01" # Learning rate: sutton and barto


def set_batch_config(config, replication_num, cross_validation_setup):
    bins = copy.deepcopy(cross_validation_setup['replications'][replication_num]['train_test_cases'])
    config["search"]["batch_sample_size"] = str(sum([len(bin) for bin in bins]))
    for i in range(len(bins)):
        bins[i] = '\n'.join(bins[i])
    bins = '\n' + '\n___\n'.join(bins)
    config["search"]["batch_instances"] = bins

def set_validate_batch_config(config, replication_num, cross_validation_setup):
    bins_all = copy.deepcopy(cross_validation_setup['all_test_cases'])
    bins_train = copy.deepcopy(cross_validation_setup['replications'][replication_num]['train_test_cases'])

    # Remove the train test cases from the bins
    for i in range(len(bins_train)):
        for j in range(len(bins_train[i])):
            bins_all[i].remove(bins_train[i][j])
    
    # Validation bins
    bins = bins_all
    config["search"]["batch_sample_size"] = str(sum([len(bin) for bin in bins]))
    for i in range(len(bins)):
        bins[i] = '\n'.join(bins[i])
    bins = '\n' + '\n___\n'.join(bins)
    config["search"]["batch_instances"] = bins

def set_budge_config(config, algo):
    if algo == 'RandomSearch':
        config["search"]["max_time"] = "7200" # 2 hours
    elif algo == 'FYPLocalSearch':
        config["search"]["max_time"] = "12600" # 3.5 hours ((2 / (3000 / 475) ) * 10); we want to do 10 batches of 475, if we do 3000 iterations in 2 hours, then we can do 10 batches in 3.5 hours

def set_fitness_config(config, is_mac=False):
    if is_mac:
        config["software"]["fitness"] = "time"
        config["software"]["run_cmd"] = ' '.join(config["software"]["run_cmd"].split(' ')[4:]) # Remove the 'perf' command

def scenario_config_setup(args, operator_selectors, search_algos, num_replications, cross_validation_setup, debug_mode=False, is_mac=False, penalise_dup_explore=False):
    for operator_selector in operator_selectors:
        for algo in search_algos:
            for replication_num in range(num_replications):
                config = configparser.ConfigParser()
                config_file = "experiments/scenario/template.ini" if not debug_mode else "experiments/scenario/debug.ini"
                config.read(config_file)
                config["search"]["penalise_dup_explore"] = str(penalise_dup_explore)
                set_fitness_config(config, is_mac)
                set_operator_selector_config(config, operator_selector)
                set_budge_config(config, algo)
                set_batch_config(config, replication_num, cross_validation_setup)
                path = f"{args.results_dir}/{algo}/{operator_selector}/trial_{replication_num}/scenario.ini"
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w') as configfile:
                    config.write(configfile)

def validate_config_setup(args, operator_selectors, search_algos, num_replications, cross_validation_setup, debug_mode=False, is_mac=False):
    for operator_selector in operator_selectors:
        for algo in search_algos:
            for replication_num in range(num_replications):
                config = configparser.ConfigParser()
                config_file = "experiments/scenario/template.ini" if not debug_mode else "experiments/scenario/debug.ini"
                config.read(config_file)
                set_fitness_config(config, is_mac)
                set_validate_batch_config(config, replication_num, cross_validation_setup)
                path = f"{args.results_dir}/{algo}/{operator_selector}/trial_{replication_num}/validate_scenario.ini"
                Path(path).parent.mkdir(parents=True, exist_ok=True)
                with open(path, 'w') as configfile:
                    config.write(configfile)

def setup(args, train_set_size, num_replications, operator_selectors, search_algos, debug_mode=False, is_mac=False, penalise_dup_explore=False):
    cross_validation_setup = cross_val_setup(args, train_set_size, num_replications)
    scenario_config_setup(args, operator_selectors, search_algos, num_replications, cross_validation_setup, debug_mode, is_mac=is_mac, penalise_dup_explore=penalise_dup_explore)
    validate_config_setup(args, operator_selectors, search_algos, num_replications, cross_validation_setup, debug_mode, is_mac=is_mac)

def exec_commands(args, commands, MAX_SUB_PROCESSES=1):
    if MAX_SUB_PROCESSES == 1: 
        for command in tqdm(commands, desc="Progress", file=open(f"{args.results_dir}/progress_logs.txt", 'a')):
            print(command, flush=True, file=open(f"{args.results_dir}/commands_logs.txt", 'a'))
            subprocess.run(command, shell=True, text=True)

        # Delete the progress file
        os.remove(f"{args.results_dir}/progress_logs.txt")
    else:         
        progress_bar = tqdm(total=len(commands), desc="Progress", file=open(f"{args.results_dir}/progress_logs.txt", 'a'))
        processes = []
        for command in commands:
            print(command, flush=True, file=open(f"{args.results_dir}/commands_logs.txt", 'a'))

            process = subprocess.Popen(command.split(' '))
            
            processes.append(process)

            if len(processes) >= MAX_SUB_PROCESSES:
                for process in processes:
                    process.wait()
                    progress_bar.update(1)
                processes = []
        
        for process in processes: # Wait off the remaining processes
            process.wait()
            progress_bar.update(1)

        progress_bar.close()
        # Delete the progress file
        os.remove(f"{args.results_dir}/progress_logs.txt")

def train(args, operator_selectors, search_algos, num_replications, MAX_SUB_PROCESSES=1):
    commands = []
    for algo in search_algos:
        for i in range(num_replications):
            if i < 5: continue
            # Train on the training folds
            for operator_selector in operator_selectors:
                scenario = f"{args.results_dir}/{algo}/{operator_selector}/trial_{i}/scenario.ini"
                command = f"python3 -m bin.local_search --scenario {scenario} --algo {algo} --seed {random.randint(1, 1000)} --output_dir {args.results_dir}/{algo}/{operator_selector}/trial_{i}"
                commands.append(command)
    
    exec_commands(args, commands, MAX_SUB_PROCESSES)
    
def test(args, operator_selectors, search_algos, num_replications, MAX_SUB_PROCESSES=1):
    commands = []
    for i in range(num_replications):
        if i < 5: continue
        # Validate on the validation folds
        for operator_selector in operator_selectors:
            for algo in search_algos:
                scenario = f"{args.results_dir}/{algo}/{operator_selector}/trial_{i}/validate_scenario.ini"
                patch = f"{args.results_dir}/{algo}/{operator_selector}/trial_{i}/logs/experiment.patch"
                command = f"python3 -m bin.revalidate_patch --scenario {scenario} --patch {patch} --output_dir {args.results_dir}/{algo}/{operator_selector}/trial_{i}"
                if os.path.exists(patch): # A valid patch exists
                    commands.append(command)

    exec_commands(args, commands, MAX_SUB_PROCESSES=1) # We run sequentially to minimise noise in the results