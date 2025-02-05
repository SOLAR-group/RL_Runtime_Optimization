from .local_search import LocalSearch, DummySearch, RandomSearch, RandomWalk, DebugSearch
from .local_search import FirstImprovement, BestImprovement, WorstImprovement, TabuSearch, FYPLocalSearch
from .local_search import FirstImprovementNoTabu, BestImprovementNoTabu
from .genetic_programming import GeneticProgramming, GeneticProgrammingConcat, GeneticProgramming1Point, GeneticProgramming2Point, GeneticProgrammingUniformConcat, GeneticProgrammingUniformInter
from .validation import ValidSearch, ValidSingle, ValidTest, ValidMinify
from .ablation import AblationAnalysis

# "final" algos only
algos = [
    DummySearch, RandomSearch, RandomWalk, DebugSearch,
    FirstImprovement, BestImprovement, WorstImprovement, TabuSearch,
    FirstImprovementNoTabu, BestImprovementNoTabu, FYPLocalSearch,
    GeneticProgrammingConcat, GeneticProgramming1Point, GeneticProgramming2Point, GeneticProgrammingUniformConcat, GeneticProgrammingUniformInter,
    ValidSingle, ValidTest, ValidMinify,
    AblationAnalysis,
]
