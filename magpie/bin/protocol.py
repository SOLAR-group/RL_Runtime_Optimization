import io
import os
import random
import pickle
from pathlib import Path
import shutil

import magpie

class BasicProtocol:
    def __init__(self):
        self.search = None
        self.program = None

    def setup(self, config):
        # Out file config
        self.search.config['final_out_dir'] = config['magpie']['final_out_dir']

        # shared parameters
        sec = config['search']
        self.search.config['warmup'] = int(sec['warmup'])
        self.search.config['warmup_strategy'] = sec['warmup_strategy']
        self.search.stop['steps'] = int(val) if (val := sec['max_steps']) else None
        self.search.stop['wall'] = int(val) if (val := sec['max_time']) else None
        self.search.stop['fitness'] = int(val) if (val := sec['target_fitness']) else None
        self.search.config['cache_maxsize'] = int(val) if (val := sec['cache_maxsize']) else 0
        self.search.config['cache_keep'] = float(sec['cache_keep'])

        self.search.config['possible_edits'] = []
        for edit in sec['possible_edits'].split():
            for klass in [*magpie.xml.edits, *magpie.line.edits, *magpie.params.edits]:
                if klass.__name__ == edit:
                    self.search.config['possible_edits'].append(klass)
                    break
            else:
                raise ValueError('Invalid config file: unknown edit type "{}" in "[software] possible_edits"'.format(edit))
        if self.search.config['possible_edits'] == []:
            raise ValueError('Invalid config file: "[search] possible_edits" must be non-empty!')
        
        # Set up our operator selector
        if 'operator_selector' not in sec:
            self.search.config['operator_selector'] = magpie.base.UniformSelector(self.search.config['possible_edits'])
        elif sec['operator_selector'] == 'UniformSelector':
            self.search.config['operator_selector'] = magpie.base.UniformSelector(self.search.config['possible_edits'])
        elif sec['operator_selector'] == 'WeightedSelector':
            initial_weights = [float(w) for w in sec['initial_weights'].split()]
            self.search.config['operator_selector'] = magpie.base.WeightedSelector(self.search.config['possible_edits'], initial_weights)
        elif sec['operator_selector'] == 'EpsilonGreedy':
            epsilon = float(sec['epsilon'])
            self.search.config['operator_selector'] = magpie.base.EpsilonGreedy(self.search.config['possible_edits'], epsilon)
        elif sec['operator_selector'] == 'ProbabilityMatching':
            p_min = float(sec['p_min'])
            self.search.config['operator_selector'] = magpie.base.ProbabilityMatching(self.search.config['possible_edits'], p_min)
        elif sec['operator_selector'] == 'UCB':
            c = float(sec['c'])
            self.search.config['operator_selector'] = magpie.base.UCB(self.search.config['possible_edits'], c)
        elif sec['operator_selector'] == 'PolicyGradient':
            alpha = float(sec['alpha'])
            self.search.config['operator_selector'] = magpie.base.PolicyGradient(self.search.config['possible_edits'], alpha)
        
        # Set up penalty for rexploring a patch: this prevents greedy hopefully
        if 'penalise_dup_explore' not in sec:
            self.search.config['penalise_dup_explore'] = False
        elif sec['penalise_dup_explore'] == 'True':
            self.search.config['penalise_dup_explore'] = True
        elif sec['penalise_dup_explore'] == 'False':
            self.search.config['penalise_dup_explore'] = False
    
        bins = [[]]
        for s in sec['batch_instances'].splitlines():
            if s == '':
                continue
            elif s == '___':
                if not bins[-1]:
                    raise ValueError('Invalid config file: empty bin in "{}"'.format(sec['search']['batch_all_samples']))
                bins.append([])
            elif s[:5] == 'file:':
                try:
                    with open(os.path.join(config['software']['path'], s[5:])) as bin_file:
                        bins[-1].extend([line.rstrip() for line in bin_file])
                except FileNotFoundError:
                    with open(s[5:]) as bin_file:
                        bins[-1].extend([line.rstrip() for line in bin_file])
            else:
                bins[-1].append(s)
        if len(bins) > 1 and not bins[-1]:
            bins.pop()
        tmp = sec['batch_shuffle'].lower()
        if tmp in ['true', 't', '1']:
            for a in bins:
                random.shuffle(a)
        elif tmp in ['false', 'f', '0']:
            pass
        else:
            raise ValueError('[search] batch_shuffle should be Boolean')
        tmp = sec['batch_bin_shuffle'].lower()
        if tmp in ['true', 't', '1']:
            random.shuffle(bins)
        elif tmp in ['false', 'f', '0']:
            pass
        else:
            raise ValueError('[search] batch_bin_shuffle should be Boolean')
        self.search.config['batch_bins'] = bins
        self.search.config['batch_sample_size'] = int(sec['batch_sample_size'])

        # local search only
        if isinstance(self.search, magpie.algo.LocalSearch):
            sec = config['search.ls']
            self.search.config['delete_prob'] = float(sec['delete_prob'])
            self.search.config['max_neighbours'] = int(val) if (val := sec['max_neighbours']) else None
            self.search.config['when_trapped'] = sec['when_trapped']
            self.search.config['accept_fail'] = sec['accept_fail']
            self.search.config['tabu_length'] = sec['tabu_length']

        # genetic programming only
        if isinstance(self.search, magpie.algo.GeneticProgramming):
            sec = config['search.gp']
            self.search.config['pop_size'] = int(sec['pop_size'])
            self.search.config['delete_prob'] = float(sec['delete_prob'])
            self.search.config['offspring_elitism'] = float(sec['offspring_elitism'])
            self.search.config['offspring_crossover'] = float(sec['offspring_crossover'])
            self.search.config['offspring_mutation'] = float(sec['offspring_mutation'])
            self.search.config['uniform_rate'] = float(sec['uniform_rate'])
            tmp = sec['batch_reset'].lower()
            if tmp in ['true', 't', '1']:
                self.search.config['batch_reset'] = True
            elif tmp in ['false', 'f', '0']:
                self.search.config['batch_reset'] = False
            else:
                raise ValueError('[search.gp] batch_reset should be Boolean')

        # minify only
        if isinstance(self.search, magpie.algo.ValidMinify):
            sec = config['search.minify']
            for key in [
                    'do_cleanup',
                    'do_rebuild',
                    'do_simplify',
            ]:
                tmp = sec[key].lower()
                if tmp in ['true', 't', '1']:
                    self.search.config[key] = True
                elif tmp in ['false', 'f', '0']:
                    self.search.config[key] = False
                else:
                    raise ValueError('[search.minify] {} should be Boolean'.format(key))
            self.search.config['round_robin_limit'] = int(sec['round_robin_limit'])

        # log config just in case
        with io.StringIO() as ss:
            config.write(ss)
            ss.seek(0)
            self.program.logger.debug('==== CONFIG ====\n{}'.format(ss.read()))

    def run(self):
        if self.program is None:
            raise AssertionError('Program not specified')
        if self.search is None:
            raise AssertionError('Search not specified')

        # init final result dict
        result = {'stop': None, 'best_patch': []}

        # setup program
        self.search.program = self.program
        try:
            self.program.ensure_contents()
        except RuntimeError as e:
            result['stop'] = str(e)

        if not result['stop']:
            # run the algorithm a single time
            self.search.run()
            result.update(self.search.report)

        logger = self.program.logger
        logger.info('')

        # print the report
        logger.info('==== REPORT ====')
        logger.info('Termination: {}'.format(result['stop']))
        for handler in logger.handlers:
            if handler.__class__.__name__ == 'FileHandler':
                logger.info('Log file: {}'.format(handler.baseFilename))
        if result['best_patch'] and result['best_patch'].edits:
            result['diff'] = self.program.diff_patch(result['best_patch'])
            base_path = os.path.join(magpie.config.log_dir, self.program.run_label)
            logger.info('Patch file: {}'.format('{}.patch'.format(base_path)))
            logger.info('Diff file: {}'.format('{}.diff'.format(base_path)))
            logger.info('Best fitness: {}'.format(result['best_fitness']))
            logger.info('Best patch: {}'.format(result['best_patch']))
            logger.info('Diff:\n{}'.format(result['diff']))
            # for convenience, save best patch and diff to separate files
            with open('{}.patch'.format(base_path), 'w') as f:
                f.write(str(result['best_patch'])+"\n")
            with open('{}.diff'.format(base_path), 'w') as f:
                f.write(result['diff'])

        # cleanup temporary software copies
        self.program.clean_work_dir()

        # Update the results with values from our experiment
        result.update(self.search.experiment_report)
        result['operator_selector'] = self.search.config['operator_selector']

        cache_info = self.search.evaluate_patch_cached.cache_info()
        # CacheInfo(hits=0, misses=3, maxsize=None, currsize=3)
        result['cache_info'] = {"hits" : cache_info.hits, "misses" : cache_info.misses, "maxsize" : cache_info.maxsize, "currsize" : cache_info.currsize}
        result['config'] = self.search.config

        # Get path of current experiment results
        experiment_path = Path(self.search.config['final_out_dir'])
        experiment_path.mkdir(parents=True, exist_ok=True)

        if isinstance(self.search, magpie.algo.validation.ValidTest):
            experiment_logs_path = (experiment_path / "validate_logs")
        else:
            experiment_logs_path = (experiment_path / "logs")

        experiment_logs_path.mkdir(parents=True, exist_ok=True)

        # Store as pickle file in experiment directory
        with open(experiment_logs_path / 'raw_result.pkl', 'wb') as file:
            pickle.dump(result, file)

        base_path = os.path.join(magpie.config.log_dir, self.program.run_label)
        if os.path.isfile(f"{base_path}.log"):
            shutil.copyfile(f"{base_path}.log", experiment_logs_path / "experiment.log")

        if os.path.isfile(f"{base_path}.diff"):
            shutil.copyfile(f"{base_path}.diff", experiment_logs_path / "experiment.diff")

        if os.path.isfile(f"{base_path}.patch"):
            shutil.copyfile(f"{base_path}.patch", experiment_logs_path / "experiment.patch")
        