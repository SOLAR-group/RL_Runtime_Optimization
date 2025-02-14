import os
import re
import shlex
import pickle

import magpie

from .. import config as magpie_config


class BasicProgram(magpie.base.AbstractProgram):
    def __init__(self, config):
        # AbstractProgram *requires* a path, a list of target files, and a list of possible edits
        if not (val := config['software']['path']):
            raise ValueError('Invalid config file: "[software] path" must be defined')
        super().__init__(config['software']['path'])
        if not (val := config['software']['target_files']):
            raise ValueError('Invalid config file: "[software] target_files" must defined')
        self.target_files = val.split()

        # engine rules
        self.engine_rules = []
        for rule in config['software']['engine_rules'].split("\n"):
            if rule: # discard potential initial empty line
                try:
                    k, v = rule.split(':')
                except ValueError:
                    raise ValueError('badly formated rule: "{}"'.format(rule))
                self.engine_rules.append((k.strip(), magpie.bin.engine_from_string(v.strip())))

        # engine config
        self.engine_config = []
        for rule in config['software']['engine_config'].split("\n"):
            if rule: # discard potential initial empty line
                try:
                    k, v = rule.split(':')
                except ValueError:
                    raise ValueError('badly formated rule: "{}"'.format(rule))
                v = v.strip()
                if v[0]+v[-1] != '[]':
                    raise ValueError('badly formated section name: "{}"'.format(rule))
                self.engine_config.append((k.strip(), config[v[1:-1]], v))

        # fitness type
        if 'fitness' not in config['software']:
            raise ValueError('Invalid config file: "[software] fitness" must be defined')
        known_fitness = ['output', 'time', 'posix_time', 'perf_time', 'perf_instructions', 'repair', 'bloat_lines', 'bloat_words', 'bloat_chars']
        if config['software']['fitness'] not in known_fitness:
            raise ValueError('Invalid config file: "[software] fitness" key must be {}'.format('/'.join(known_fitness)))
        self.fitness_type = config['software']['fitness']

        # execution-related parameters
        self.init_performed = False
        self.init_cmd = None
        self.init_timeout = None
        self.setup_performed = False
        self.setup_cmd = None
        self.setup_timeout = None
        self.setup_lengthout = None
        self.compile_cmd = None
        self.compile_timeout = None
        self.compile_lengthout = None
        self.test_cmd = None
        self.test_timeout = None
        self.test_lengthout = None
        self.run_cmd = None
        self.run_timeout = None
        self.run_lengthout = None
        self.batch_timeout = None
        self.batch_lengthout = None

        # init
        if 'init_cmd' in config['software']:
            if config['software']['init_cmd'].lower() in ['', 'none']:
                self.init_cmd = None
            else:
                self.init_cmd = config['software']['init_cmd']
        if 'init_timeout' in config['software']:
            if config['software']['init_timeout'].lower() in ['', 'none']:
                self.init_timeout = None
            else:
                self.init_timeout = float(config['software']['init_timeout'])
        if 'init_lengthout' in config['software']:
            if config['software']['init_lengthout'].lower() in ['', 'none']:
                self.init_lengthout = None
            else:
                self.init_lengthout = int(config['software']['init_lengthout'])

        # setup
        if 'setup_cmd' in config['software']:
            if config['software']['setup_cmd'].lower() in ['', 'none']:
                self.setup_cmd = None
            else:
                self.setup_cmd = config['software']['setup_cmd']
        if 'setup_timeout' in config['software']:
            if config['software']['setup_timeout'].lower() in ['', 'none']:
                self.setup_timeout = None
            else:
                self.setup_timeout = float(config['software']['setup_timeout'])
        if 'setup_lengthout' in config['software']:
            if config['software']['setup_lengthout'].lower() in ['', 'none']:
                self.setup_lengthout = None
            else:
                self.setup_lengthout = int(config['software']['setup_lengthout'])

        # compile
        if 'compile_cmd' in config['software']:
            if config['software']['compile_cmd'].lower() in ['', 'none']:
                self.compile_cmd = None
            else:
                self.compile_cmd = config['software']['compile_cmd']
        if 'compile_timeout' in config['software']:
            if config['software']['compile_timeout'].lower() in ['', 'none']:
                self.compile_timeout = None
            else:
                self.compile_timeout = float(config['software']['compile_timeout'])
        if 'compile_lengthout' in config['software']:
            if config['software']['compile_lengthout'].lower() in ['', 'none']:
                self.compile_lengthout = None
            else:
                self.compile_lengthout = int(config['software']['compile_lengthout'])

        # test
        if 'test_cmd' in config['software']:
            if config['software']['test_cmd'].lower() in ['', 'none']:
                self.test_cmd = None
            else:
                self.test_cmd = config['software']['test_cmd']
        if 'test_timeout' in config['software']:
            if config['software']['test_timeout'].lower() in ['', 'none']:
                self.test_timeout = None
            else:
                self.test_timeout = float(config['software']['test_timeout'])
        if 'test_lengthout' in config['software']:
            if config['software']['test_lengthout'].lower() in ['', 'none']:
                self.test_lengthout = None
            else:
                self.test_lengthout = int(config['software']['test_lengthout'])

        # run
        if 'run_cmd' in config['software']:
            if config['software']['run_cmd'].lower() in ['', 'none']:
                self.run_cmd = None
            else:
                self.run_cmd = config['software']['run_cmd']
        if 'run_timeout' in config['software']:
            if config['software']['run_timeout'].lower() in ['', 'none']:
                self.run_timeout = None
            else:
                self.run_timeout = float(config['software']['run_timeout'])
        if 'run_lengthout' in config['software']:
            if config['software']['run_lengthout'].lower() in ['', 'none']:
                self.run_lengthout = None
            else:
                self.run_lengthout = int(config['software']['run_lengthout'])

        # batch parameters
        self.batch = [''] # default initial batch: single empty instance
        self.batch_fitness_strategy = config['software']['batch_fitness_strategy']
        known_strategies = ['sum', 'average', 'median']
        if self.batch_fitness_strategy not in known_strategies:
            raise ValueError('Invalid config file: "[software] batch_fitness_strategy" key must be {}'.format('/'.join(known_strategies)))
        self.batch_bin_fitness_strategy = config['software']['batch_fitness_strategy']
        known_strategies = ['aggregate', 'sum', 'average', 'median', 'q10', 'q25', 'q75', 'q90']
        if self.batch_fitness_strategy not in known_strategies:
            raise ValueError('Invalid config file: "[software] batch_bin_fitness_strategy" key must be {}'.format('/'.join(known_strategies)))
        if 'batch_timeout' in config['software']:
            if config['software']['batch_timeout'].lower() in ['', 'none']:
                self.batch_timeout = None
            else:
                self.batch_timeout = float(config['software']['batch_timeout'])
        if 'batch_lengthout' in config['software']:
            if config['software']['batch_lengthout'].lower() in ['', 'none']:
                self.batch_lengthout = None
            else:
                self.batch_lengthout = int(config['software']['batch_lengthout'])

    def ensure_contents(self):
        if not self.contents:
            # take care of cmd_init first thing
            if self.init_cmd:
                cwd = os.getcwd()
                try:
                    os.chdir(self.path)
                    timeout = self.init_timeout or magpie_config.default_timeout
                    lengthout = self.init_lengthout or magpie_config.default_lengthout
                    exec_result = self.exec_cmd(shlex.split(self.init_cmd),
                                                timeout=timeout,
                                                lengthout=lengthout)
                    run_result = magpie.base.RunResult(exec_result.status)
                    if run_result.status == 'SUCCESS':
                        self.process_init_exec(run_result, exec_result)
                    if run_result.status != 'SUCCESS':
                        run_result.status = f'INIT_{run_result.status}'
                        run_result.last_exec = exec_result
                        self.diagnose_error(run_result)
                        raise RuntimeError('(cmd_init) failed to init target software')
                finally:
                    os.chdir(cwd)

            # reset after cmd_init
            self.reset_contents()

    def get_engine(self, target_file):
        for (pattern, engine) in self.engine_rules:
            if any([target_file == pattern,
                    pattern == '*',
                    pattern.startswith('*') and target_file.endswith(pattern[1:]),
            ]):
                return engine()
        raise RuntimeError('Unknown engine for target file {}'.format(target_file))

    def configure_engine(self, engine, target_file):
        for (pattern, config_section, section_name) in self.engine_config:
            if any([target_file == pattern,
                    pattern == '*',
                    pattern.startswith('*') and target_file.endswith(pattern[1:]),
            ]):
                if isinstance(engine, magpie.xml.XmlEngine):
                    magpie.bin.setup_xml_engine(engine, config_section, section_name)
                elif isinstance(engine, magpie.params.AbstractParamsEngine):
                    magpie.bin.setup_params_engine(engine, config_section, section_name)
                return

    def evaluate_contents(self, new_contents, cached_run=None):
        # write if batch unsynced
        if cached_run is None or not set(inst for b in self.batch for inst in b).issubset(cached_run.cache.keys()):
            self.write_contents(new_contents)
        return self.evaluate_local(cached_run)

    def evaluate_local(self, cached_run=None):
        # check batch sync
        if cached_run is not None and set(inst for b in self.batch for inst in b).issubset(cached_run.cache.keys()):
            self.process_batch_final(cached_run)
            return cached_run
        # otherwise
        cwd = os.getcwd()
        work_path = os.path.join(self.work_dir, self.basename)
        run_result = cached_run or magpie.base.RunResult('UNKNOWN_ERROR')

        try:
            # go to work directory
            os.chdir(work_path)

            # one-time setup
            if not self.setup_performed:
                self.setup_performed = True

                # make sure this is the unmodified software
                for filename in self.target_files:
                    engine = self.get_engine(filename)
                    assert engine.dump(self.local_contents[filename]) == engine.dump(self.contents[filename])

                # run "[software] setup_cmd" if provided
                if self.setup_cmd:
                    # setup
                    cli = self.compute_local_cli('setup')
                    setup_cmd = self.setup_cmd.strip()
                    if '{PARAMS}' in self.setup_cmd:
                        setup_cmd = setup_cmd.replace('{PARAMS}', cli)
                    else:
                        setup_cmd = '{} {}'.format(setup_cmd, cli)
                    timeout = self.setup_timeout or magpie_config.default_timeout
                    lengthout = self.setup_lengthout or magpie_config.default_lengthout
                    exec_result = self.exec_cmd(shlex.split(setup_cmd),
                                                timeout=timeout,
                                                lengthout=lengthout)
                    run_result.status = exec_result.status
                    run_result.last_exec = exec_result
                    if run_result.status == 'SUCCESS':
                        self.process_setup_exec(run_result, exec_result)
                    if run_result.status != 'SUCCESS':
                        run_result.status = 'SETUP_{}'.format(run_result.status)
                        return run_result

                # sync work directory
                self.sync_folder(self.path, work_path)

            # run "[software] compile_cmd" if provided
            if self.compile_cmd:
                cli = self.compute_local_cli('compile')
                compile_cmd = self.compile_cmd.strip()
                if '{PARAMS}' in self.compile_cmd:
                    compile_cmd = compile_cmd.replace('{PARAMS}', cli)
                else:
                    compile_cmd = '{} {}'.format(compile_cmd, cli)
                timeout = self.compile_timeout or magpie_config.default_timeout
                lengthout = self.compile_lengthout or magpie_config.default_lengthout
                exec_result = self.exec_cmd(shlex.split(compile_cmd),
                                            timeout=timeout,
                                            lengthout=lengthout)
                run_result.status = exec_result.status
                run_result.last_exec = exec_result
                if run_result.status == 'SUCCESS':
                    self.process_compile_exec(run_result, exec_result)
                if run_result.status != 'SUCCESS':
                    run_result.status = 'COMPILE_{}'.format(run_result.status)
                    return run_result

            # run "[software] test_cmd" if provided
            if self.test_cmd:
                assert False, "we should not be here as we do not support a test command anymore; everything is done through the run command"
                cli = self.compute_local_cli('test')
                test_cmd = self.test_cmd.strip()
                if '{PARAMS}' in self.test_cmd:
                    test_cmd = test_cmd.replace('{PARAMS}', cli)
                else:
                    test_cmd = '{} {}'.format(test_cmd, cli)
                timeout = self.test_timeout or magpie_config.default_timeout
                lengthout = self.test_lengthout or magpie_config.default_lengthout
                exec_result = self.exec_cmd(shlex.split(test_cmd),
                                            timeout=timeout,
                                            lengthout=lengthout)
                run_result.status = exec_result.status
                run_result.last_exec = exec_result
                if run_result.status == 'SUCCESS':
                    self.process_test_exec(run_result, exec_result)
                if run_result.status != 'SUCCESS':
                    run_result.status = 'TEST_{}'.format(run_result.status)
                    return run_result

            # when fitness is computed from test_cmd, run_cmd is irrelevant
            if self.fitness_type in ['repair', 'bloat_lines', 'bloat_words', 'bloat_chars']:
                return run_result

            # run "[software] run_cmd" if provided
            if self.run_cmd:
                cli = self.compute_local_cli('run')
                timeout = self.run_timeout or magpie_config.default_timeout
                lengthout = self.run_lengthout or magpie_config.default_lengthout
                batch_timeout = self.batch_timeout
                batch_lengthout = self.batch_lengthout
                insts = [inst for b in self.batch for inst in b]
                for inst in insts:
                    if inst in run_result.cache.keys():
                        continue
                    run_cmd = self.run_cmd.strip()
                    if '{INST}' in self.run_cmd:
                        run_cmd = run_cmd.replace('{INST}', inst)
                    else:
                        run_cmd = '{} {}'.format(run_cmd, inst)
                    if '{PARAMS}' in self.run_cmd:
                        run_cmd = run_cmd.replace('{PARAMS}', cli)
                    else:
                        run_cmd = '{} {}'.format(run_cmd, cli)
                    exec_result = self.exec_cmd(shlex.split(run_cmd),
                                                timeout=timeout,
                                                lengthout=lengthout)
                    run_result.status = exec_result.status
                    run_result.last_exec = exec_result
                    if run_result.status == 'SUCCESS':
                        self.process_run_exec(run_result, exec_result)
                    self.process_batch_single(run_result, inst)
                    if run_result.status != 'SUCCESS':
                        run_result.status = 'RUN_{}'.format(run_result.status)
                        break
                    elif batch_timeout:
                        batch_timeout -= exec_result.runtime
                        if batch_timeout < 0:
                            run_result.status = 'BATCH_TIMEOUT'
                            break
                    elif batch_lengthout:
                        batch_lengthout -= exec_result.output_length
                        if batch_lengthout < 0:
                            run_result.status = 'BATCH_LENGTHOUT'
                            break

        finally:
            # make sure to go back to main directory
            os.chdir(cwd)

        # final process
        self.process_batch_final(run_result)
        return run_result

    def process_init_exec(self, run_result, exec_result):
        # "[software] init_cmd" must yield nonzero return code
        if exec_result.return_code != 0:
            run_result.status = 'CODE_ERROR'

    def process_setup_exec(self, run_result, exec_result):
        # "[software] setup_cmd" must yield nonzero return code
        if exec_result.return_code != 0:
            run_result.status = 'CODE_ERROR'

    def process_compile_exec(self, run_result, exec_result):
        # "[software] compile_cmd" must yield nonzero return code
        if exec_result.return_code != 0:
            run_result.status = 'CODE_ERROR'

    def process_test_exec(self, run_result, exec_result):
        # if "[software] fitness" is "repair", we check STDOUT for the number of failed test cases
        if self.fitness_type == 'repair':
            stdout = exec_result.stdout.decode(magpie.config.output_encoding)
            for fail_regexp, total_regexp in [
                (r'Failures: (\d+)\b', r'^Tests run: (\d+)\b'), # junit
                (r'\b(\d+) failed', r'^collected (\d+) items'), # pytest
                (r' (\d+) (?:failures|errors)', r'^(\d+) runs,'), # minitest
            ]:
                fail_matches = re.findall(fail_regexp, stdout, re.MULTILINE)
                total_matches = re.findall(total_regexp, stdout, re.MULTILINE)
                n_fail = 0
                n_total = 0
                for m in fail_matches:
                    try:
                        n_fail += float(m)
                    except ValueError:
                        run_result.status = 'PARSE_ERROR'
                for m in total_matches:
                    try:
                        n_total += float(m)
                    except ValueError:
                        run_result.status = 'PARSE_ERROR'
                if n_total > 0:
                    run_result.fitness = round(100*n_fail/n_total, 2)
                    break
            else:
                run_result.status = 'PARSE_ERROR'

        # in all other cases "[software] test_cmd" must just yield nonzero return code
        elif exec_result.return_code != 0:
            run_result.status = 'CODE_ERROR'
            return

        # if "[software] fitness" is one of "bloat_*", we can count here
        if self.fitness_type == 'bloat_lines':
            run_result.fitness = 0
            for filename in self.target_files:
                with open(self.get_engine(filename).renamed_contents_file(filename)) as target:
                    run_result.fitness += len(target.readlines())
        elif self.fitness_type == 'bloat_words':
            run_result.fitness = 0
            for filename in self.target_files:
                with open(self.get_engine(filename).renamed_contents_file(filename)) as target:
                    run_result.fitness += sum(len(s.split()) for s in target.readlines())
        elif self.fitness_type == 'bloat_chars':
            run_result.fitness = 0
            for filename in self.target_files:
                with open(self.get_engine(filename).renamed_contents_file(filename)) as target:
                    run_result.fitness += sum(len(s) for s in target.readlines())

    def process_run_exec(self, run_result, exec_result):
        # in all cases "[software] run_cmd" must yield nonzero return code
        if exec_result.return_code != 0:
            run_result.status = 'CODE_ERROR'
            return

        # if "[software] fitness" is "output", we check STDOUT for the string "MAGPIE_FITNESS:"
        if self.fitness_type == 'output':
            stdout = exec_result.stdout.decode(magpie_config.output_encoding)
            m = re.search('MAGPIE_FITNESS: (.*)', stdout)
            if m:
                try:
                    run_result.fitness = float(m.group(1))
                except ValueError:
                    run_result.status = 'PARSE_ERROR'
            else:
                run_result.status = 'PARSE_ERROR'

        # if "[software] fitness" is "time", we just use time as seen by the main Python process
        elif self.fitness_type == 'time':
            run_result.fitness = round(exec_result.runtime, 4)

        # if "[software] fitness" is "posix_time", we assume a POSIX-compatible output on STDERR
        elif self.fitness_type == 'posix_time':
            stderr = exec_result.stderr.decode(magpie_config.output_encoding)
            m = re.search('real (.*)', stderr)
            if m:
                try:
                    run_result.fitness = float(m.group(1))
                except ValueError:
                    run_result.status = 'PARSE_ERROR'
            else:
                run_result.status = 'PARSE_ERROR'

        # if "[software] fitness" is "perf_time", we assume a perf-like output on STDERR
        elif self.fitness_type == 'perf_time':
            stderr = exec_result.stderr.decode(magpie_config.output_encoding)
            m = re.search('(.*) seconds time elapsed', stderr)
            if m:
                try:
                    run_result.fitness = round(float(m.group(1)), 4)
                except ValueError:
                    run_result.status = 'PARSE_ERROR'
            else:
                run_result.status = 'PARSE_ERROR'

        # if "[software] fitness" is "perf_instructions", we assume a perf-like output on STDERR
        elif self.fitness_type == 'perf_instructions':
            stderr = exec_result.stderr.decode(magpie_config.output_encoding)
            m = re.search('(.*) instructions', stderr)
            if m:
                try:
                    run_result.fitness = int(m.group(1).replace(',', ''))
                except ValueError:
                    run_result.status = 'PARSE_ERROR'
            else:
                run_result.status = 'PARSE_ERROR'

    def process_batch_single(self, run_result, inst):
        run_result.cache[inst] = (run_result.status, run_result.fitness)
        self.logger.debug('EXEC> {} {} {}'.format(inst, run_result.status, run_result.fitness))

    def process_batch_final(self, run_result):
        tmp = []
        fit = []
        for b in self.batch:
            bin_fitness = []
            for inst in b:
                status, fitness = run_result.cache[inst]
                if status != 'SUCCESS':
                    # TODO: penalised fitness
                    run_result.fitness = None
                    return
                bin_fitness.append(fitness)
            multi = isinstance(bin_fitness[0], list)
            if self.batch_bin_fitness_strategy == 'aggregate':
                tmp.extend(bin_fitness)
            else:
                for a in ([list(a) for a in zip(*bin_fitness)] if multi else [bin_fitness]):
                    precision = max(len(str(float(x)).split('.')[1]) for x in a)
                    if self.batch_bin_fitness_strategy == 'sum':
                        v = sum(a)
                    elif self.batch_bin_fitness_strategy == 'average':
                        v = sum(a)/len(a)
                        precision += 1
                    elif self.batch_bin_fitness_strategy == 'median':
                        if len(a) % 2 == 0:
                            v = sorted(a)[len(a)//2]
                        else:
                            v = sum(sorted(a)[len(a)//2:len(a)//2+2])/2
                            precision += 1
                    elif self.batch_bin_fitness_strategy == 'q10':
                        if len(a) % 10 == 0:
                            v = sorted(a)[len(a)//10]
                        else:
                            v = sum(sorted(a)[len(a)//10:len(a)//10+2])/2
                            precision += 1
                    elif self.batch_bin_fitness_strategy == 'q25':
                        if len(a) % 4 == 0:
                            v = sorted(a)[len(a)//4]
                        else:
                            v = sum(sorted(a)[len(a)//10:len(a)//10+2])/2
                            precision += 1
                    elif self.batch_bin_fitness_strategy == 'q75':
                        if len(a) % 4 == 0:
                            v = sorted(a)[3*len(a)//4]
                        else:
                            v = sum(sorted(a)[3*len(a)//4:3*len(a)//4+2])/2
                            precision += 1
                    elif self.batch_bin_fitness_strategy == 'q90':
                        if len(a) % 10 == 0:
                            v = sorted(a)[len(a)//10]
                        else:
                            v = sum(sorted(a)[9*len(a)//10:9*len(a)//10+2])/2
                            precision += 1
                    tmp.append(round(v, precision))
        for a in ([list(a) for a in zip(*tmp)] if multi else [tmp]):
            precision = max(len(str(float(x)).split('.')[1]) for x in a)
            if self.batch_fitness_strategy == 'sum':
                v = sum(a)
            elif self.batch_fitness_strategy == 'average':
                v = sum(a)/len(a)
                precision += 1
            elif self.batch_fitness_strategy == 'median':
                if len(a) % 2 == 0:
                    v = sorted(a)[len(a)//2]
                else:
                    v = sum(sorted(a)[len(a)//2:len(a)//2+2])/2
                    precision += 1
            fit.append(round(v, precision))
        run_result.fitness = fit if multi else fit[0]

    def diagnose_error(self, run):
        self.logger.info('!*'*40)
        self.logger.info('Unable to run and evaluate the target software.')
        self.logger.info('Self-diagnostic:')
        self.self_diagnostic(run)
        self.logger.info('!*'*40)
        if run.last_exec is not None:
            self.logger.info('CWD: {}'.format(os.path.join(self.work_dir, self.basename)))
            self.logger.info('CMD: {}'.format(run.last_exec.cmd))
            self.logger.info('STATUS: {}'.format(run.last_exec.status))
            self.logger.info('RETURN_CODE: {}'.format(run.last_exec.return_code))
            self.logger.info('RUNTIME: {}'.format(run.last_exec.runtime))
            try:
                s = run.last_exec.stdout.decode(magpie_config.output_encoding)
                self.logger.info('STDOUT: (see log file)')
                self.logger.debug('STDOUT:\n{}'.format(s))
            except UnicodeDecodeError:
                self.logger.info('STDOUT: (failed to decode to: {})\n{}'.format(magpie_config.output_encoding, run.last_exec.stdout))
            try:
                s = run.last_exec.stderr.decode(magpie_config.output_encoding)
                self.logger.info('STDERR: (see log file)')
                self.logger.debug('STDERR:\n{}'.format(s))
            except UnicodeDecodeError:
                s = magpie_config.output_encoding
                self.logger.info('STDERR: (failed to decode to: {})\n{}'.format(magpie_config.output_encoding, run.last_exec.stderr))
            self.logger.info('!*'*40)

    def self_diagnostic(self, run):
        for step in ['init', 'setup', 'compile', 'test', 'run']:
            if run.status == '{}_CLI_ERROR'.format(step.upper()):
                self.logger.info('Unable to run the "{}_cmd" command'.format(step))
                self.logger.info('--> there might be a typo (try it manually)')
                self.logger.info('--> your command might not be found (check your PATH)')
                self.logger.info('--> it might not run from the correct directory (check CWD below)')
            if run.status == '{}_CODE_ERROR'.format(step.upper()):
                self.logger.info('The "{}_cmd" command failed with a nonzero exit code'.format(step))
                self.logger.info('--> try to run it manually')
            if run.status == '{}_PARSE_ERROR'.format(step.upper()):
                self.logger.info('The "{}_cmd" STDOUT/STDERR was invalid'.format(step))
                self.logger.info('--> try to run it manually')
            if run.status == '{}_TIMEOUT'.format(step.upper()):
                self.logger.info('The "{}_cmd" command took too long to run'.format(step))
                self.logger.info('--> consider increasing "{}_timeout"'.format(step))
            if run.status == '{}_LENGTHOUT'.format(step.upper()):
                self.logger.info('The "{}_cmd" command generated too much output'.format(step))
                self.logger.info('--> consider increasing "{}_lengthout"'.format(step))
        if run.status == 'BATCH_TIMEOUT'.format(step.upper()):
                self.logger.info('Batch execution of "run_cmd" took too long to run'.format(step))
                self.logger.info('--> consider increasing "batch_timeout"'.format(step))
        if run.status == 'BATCH_LENGTHOUT'.format(step.upper()):
                self.logger.info('Batch execution of "run_cmd" generated too much output'.format(step))
                self.logger.info('--> consider increasing "batch_lengthout"'.format(step))
