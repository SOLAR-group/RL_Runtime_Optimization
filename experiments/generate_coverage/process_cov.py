import subprocess
import json
import os
import shutil
from functools import cache
from itertools import combinations
import re

NUM_REP = 10

root_dir = os.getcwd()
out_path = root_dir + "/experiments/generate_coverage/coverage_data"

@cache
def get_converge_val(bin_val): # takes a full test path
    get_name = lambda x: f"{x.split('/')[-1].split(' ')[0]}.txt"
    
    path_to_coverage = f"{out_path}/{get_name(bin_val)}"
    if not os.path.exists(path_to_coverage):
        raise RuntimeError(f"Coverage file for {bin_val} does not exist")

    with open(path_to_coverage, 'r') as file:
        file_contents = file.read()    

    # Regex
    pattern = r'(?<=,)\s*\w+|\w+\s*(?=,)'
    matches = re.findall(pattern, file_contents)
    matches = {int(branch_num) for branch_num in matches}
    
    return matches

def strip_os_path(bins):
    result = []
    for bin in bins:
        result.append(['/'.join(test_case.split('/')[-2:]) for test_case in bin])
    
    final_result = []
    for bin in result:
        final_result.append([test_case.split(' ')[0] for test_case in bin])

    return final_result

def select_tests_to_maximize_coverage(bin, branches_covered):
    current_a = None
    current_b = None
    current_max_set = set()

    for test_case_a, test_case_b in combinations(bin, 2):
        branches_covered_a = get_converge_val(test_case_a)
        branches_covered_b = get_converge_val(test_case_b)
        current_covered_set = branches_covered_a | branches_covered_b | branches_covered
        if len(current_covered_set) > len(current_max_set):
            current_a = test_case_a
            current_b = test_case_b
            current_max_set = current_covered_set
    return current_max_set, [current_a, current_b]

def generate_single_replication_test_suite(bins):
    branches_covered = set()
    new_bins = []
    for bin in bins:
        print(f"Before branches covered: {len(branches_covered)}")
        branches_covered, tests = select_tests_to_maximize_coverage(bin, branches_covered)
        print(f"Selected tests: {tests}")
        print(f"After branches covered: {len(branches_covered)}")

        new_bins.append(tests)

    print("-------------------")
    print(f"New bins: {new_bins}")
    return new_bins, branches_covered

if __name__ == "__main__":

    # Generate the folds
    with open('examples/code/benchmark/sat_uniform.json', 'r') as file:
        bins = json.load(file)

    # Use absolute paths for test cases & SAT/UNSAT label
    in_path = root_dir + "/examples/code/benchmark"
    for bin in bins:
        for i, elem in enumerate(bin):
            test_case_type = 'SAT' if elem.split('/')[-1].count('u') == 1 else 'UNSAT'
            bin[i] = f"{in_path}/{elem} {test_case_type}"
    
    # Get all branches covered
    all_branches = set()
    for bin in bins:
        for test_case in bin:
            branches_covered = get_converge_val(test_case)
            print(f"Test case: {test_case} has {len(branches_covered)} branches covered")
            all_branches = all_branches.union(branches_covered)
    print(f"Total branches covered: {len(all_branches)}")

    # Generate a single replication test suite
    result_out = "experiments/generate_coverage/max_coverage_test_suites.json"
    result = {}

    total_test_case_visited = [set() for _ in bins]
    for rep_num in range(NUM_REP):
        not_visited = [set(bin_vals) - visited_bin_vals for bin_vals, visited_bin_vals in zip(bins, total_test_case_visited)]
        print("debug", len(not_visited), len(not_visited[0]))
        replication_bins, branches_covered = generate_single_replication_test_suite(not_visited)
        assert len(branches_covered) == len(all_branches), "Each replication should cover all branches"
        result[rep_num] = strip_os_path(replication_bins)

        # Update the total test case visited
        for replication_bin, total_bin in zip(replication_bins, total_test_case_visited):
            total_bin.update(replication_bin)
    
    with open(result_out, 'w') as file:
        json.dump(result, file, indent=4)