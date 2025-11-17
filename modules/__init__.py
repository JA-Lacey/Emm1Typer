"""
Emm1typer Modules

Focused modules for emm1 lineage typing, MLST analysis, and emmtyping.
"""

__version__ = "1.0.0"
__author__ = "Genomic Implementation Team"

# Import all modules for easy access
from .config_manager import ConfigManager
from .dependency_checker import DependencyChecker
from .lineage_typer import LineageTyper
from .mlst_analyzer import MLSTAnalyzer
from .emm_typer import EmmTyper
from .results_analyzer import ResultsAnalyzer
from .report_generator import ReportGenerator

__all__ = [
    'ConfigManager',
    'DependencyChecker', 
    'LineageTyper',
    'MLSTAnalyzer',
    'EmmTyper',
    'ResultsAnalyzer',
    'ReportGenerator'
]