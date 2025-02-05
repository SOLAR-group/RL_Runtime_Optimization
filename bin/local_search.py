import argparse
import configparser
import pathlib
import traceback
import os
import magpie


# ================================================================================
# Main function
# ================================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Magpie local search')
    parser.add_argument('--scenario', type=pathlib.Path, required=True)
    parser.add_argument('--algo', type=str, required=True)
    parser.add_argument('--output_dir', type=pathlib.Path, required=True)
    parser.add_argument('--seed', type=int)
    args = parser.parse_args()

    # read config file
    config = configparser.ConfigParser()
    config.read_dict(magpie.bin.default_config)
    config.read(args.scenario)
    magpie.bin.pre_setup(config)

    # select LS algorithm
    if args.algo is not None:
        config['search']['algorithm'] = args.algo
    if config['search']['algorithm']:
        algo = magpie.bin.algo_from_string(config['search']['algorithm'])
        if not issubclass(algo, magpie.algo.LocalSearch):
            raise RuntimeError('{} is not a local search'.format(args.algo))
    else:
        config['search']['algorithm'] = 'FirstImprovement'
        algo = magpie.algo.FirstImprovement

    # Set the seed
    if args.seed is not None:
        config['magpie']['seed'] = str(args.seed)
    
    # setup output directory
    config['magpie']['final_out_dir'] = str(args.output_dir)

    # setup protocol
    magpie.bin.setup(config)
    protocol = magpie.bin.protocol_from_string(config['search']['protocol'])()
    protocol.search = algo()
    protocol.program = magpie.bin.program_from_string(config['software']['program'])(config)
    protocol.setup(config)

    # run experiments
    try:
        protocol.run()
    except Exception:
        if not os.path.exists(args.output_dir):
            os.makedirs(args.output_dir)
        with open(f"{str(args.output_dir)}/error.txt", 'w') as f:
            print(traceback.format_exc(), file=f)
        raise
