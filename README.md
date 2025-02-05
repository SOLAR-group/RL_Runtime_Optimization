# RL Runtime Optimization

This repository includes the replication package for the experiments. The results from the paper are present in `FINAL_RESULTS`.

This experiment replication package was built upon the [Magpie](https://github.com/bloa/magpie) framework.

## Replicating The Experiments

Make sure you have all the python dependencies listed below.

### Run experiments
```bash
bash experiments/run.sh &
```

> Note that running took about 50 hours 40 mins on our hardware specs. 

All the log files should go in the `experiments/results` folder.

### Produce graphs and metrics

Change the `RESULT_DIR` variable in the `experiments/process_results/process_official_final.ipynb` notebook to point your results folder (e.g, `experiments/results`). Then run all the notebook cells. The metrics and graphs should be computed automatically.

## Software Versions Used
- g++ 11.4.0
- perf 6.5.13
- Python 3.10.12

## Python Requirements
- numpy
- gcovr
- tqdm
- notebook
- pandas
- scipy
- matplotlib
