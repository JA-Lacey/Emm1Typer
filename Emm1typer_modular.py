#!/usr/bin/env python3
"""
Emm1typer - Modular version

A comprehensive tool for emm1 lineage typing, MLST analysis, and emmtyping of 
Streptococcus pyogenes isolates.

This refactored version uses focused modules for easier maintenance and modification.
"""

import argparse
import sys
from pathlib import Path

# Import all the focused modules
from modules.config_manager import ConfigManager
from modules.dependency_checker import DependencyChecker
from modules.lineage_typer import LineageTyper
from modules.mlst_analyzer import MLSTAnalyzer
from modules.emm_typer import EmmTyper
from modules.results_analyzer import ResultsAnalyzer
from modules.report_generator import ReportGenerator


class Emm1TyperOrchestrator:
    """Main orchestrator that coordinates all analysis modules"""
    
    def __init__(self, reference_dir, output_dir="emm1typer_output", threads=8, parallel_jobs=10):
        """
        Initialize Emm1typer orchestrator
        
        Args:
            reference_dir: Path to reference data directory
            output_dir: Output directory for results
            threads: Number of threads for analysis tools
            parallel_jobs: Number of parallel jobs for mykrobe
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize configuration manager
        self.config_manager = ConfigManager(reference_dir)
        
        # Initialize analysis modules
        self.lineage_typer = LineageTyper(self.config_manager, output_dir, parallel_jobs)
        self.mlst_analyzer = MLSTAnalyzer(output_dir, threads)
        self.emm_typer = EmmTyper(output_dir, threads)
        self.results_analyzer = ResultsAnalyzer(self.config_manager, output_dir)
        self.report_generator = ReportGenerator(output_dir)
        
        # Initialize dependency checker
        self.dependency_checker = DependencyChecker()
    
    def check_dependencies(self):
        """Check all required dependencies"""
        self.dependency_checker.check_dependencies()
    
    def run_lineage_analysis(self, reads_file):
        """
        Run emm1 lineage typing analysis
        
        Args:
            reads_file: Path to reads input file
            
        Returns:
            bool: Success status
        """
        print("\n" + "="*50)
        print("RUNNING EMM1 LINEAGE TYPING")
        print("="*50)
        
        return self.lineage_typer.process_reads(reads_file)
    
    def run_contig_analysis(self, contigs_file):
        """
        Run MLST and emmtyping analysis on contigs
        
        Args:
            contigs_file: Path to contigs input file
            
        Returns:
            tuple: (mlst_success, emmtyper_success)
        """
        print("\n" + "="*50)
        print("RUNNING CONTIG ANALYSIS")
        print("="*50)
        
        # Run MLST analysis
        print("\nRunning MLST analysis...")
        mlst_success = self.mlst_analyzer.process_contigs(contigs_file)
        
        # Run emmtyper analysis
        print("\nRunning emmtyper analysis...")
        emmtyper_success = self.emm_typer.process_contigs(contigs_file)
        
        return mlst_success, emmtyper_success
    
    def analyze_results(self):
        """
        Analyze all results and filter by acceptable types
        
        Returns:
            dict: Analysis summary
        """
        print("\n" + "="*50)
        print("ANALYZING RESULTS")
        print("="*50)
        
        return self.results_analyzer.get_analysis_summary()
    
    def generate_reports(self, analysis_summary=None):
        """
        Generate comprehensive summary reports
        
        Args:
            analysis_summary: Dictionary with analysis results (optional)
        """
        print("\n" + "="*50)
        print("GENERATING REPORTS")
        print("="*50)
        
        # Get tool versions for the report
        dependency_versions = self.dependency_checker.get_tool_versions()
        
        # Generate summary report
        self.report_generator.generate_summary_report(analysis_summary, dependency_versions)
    
    def run_complete_analysis(self, reads_file=None, contigs_file=None):
        """
        Run complete analysis pipeline
        
        Args:
            reads_file: Path to reads input file (optional)
            contigs_file: Path to contigs input file (optional)
        """
        print("Starting Emm1typer analysis...")
        print(f"Output directory: {self.output_dir}")
        
        success_flags = {}
        
        # Run lineage analysis if reads provided
        if reads_file:
            success_flags['lineage'] = self.run_lineage_analysis(reads_file)
        
        # Run contig analysis if contigs provided
        if contigs_file:
            mlst_success, emmtyper_success = self.run_contig_analysis(contigs_file)
            success_flags['mlst'] = mlst_success
            success_flags['emmtyper'] = emmtyper_success
        
        # Analyze results
        analysis_summary = self.analyze_results()
        
        # Generate reports
        self.generate_reports(analysis_summary)
        
        # Print final summary
        print("\n" + "="*50)
        print("ANALYSIS COMPLETE")
        print("="*50)
        
        for analysis_type, success in success_flags.items():
            status = "✓ SUCCESS" if success else "✗ FAILED"
            print(f"{analysis_type.upper()}: {status}")
        
        print(f"\nResults saved to: {self.output_dir}")


def main():
    parser = argparse.ArgumentParser(
        description="Emm1typer: Modular emm1 lineage typing, MLST, and emmtyping analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process reads only (emm1 lineage typing)
  python Emm1typer_modular.py --reads reads.tab --reference-dir ./reference_data

  # Process contigs only (MLST + emmtyping)  
  python Emm1typer_modular.py --contigs contigs.tab --reference-dir ./reference_data

  # Process both reads and contigs (complete analysis)
  python Emm1typer_modular.py --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data

Input file formats:
  reads.tab: Strain_ID<tab>reads1_path<tab>reads2_path
  contigs.tab: Strain_ID<tab>contigs_path

Modular Design:
  This version uses focused modules in the modules/ directory:
  - config_manager.py: Configuration and reference file management
  - dependency_checker.py: External tool validation
  - lineage_typer.py: emm1 lineage typing using mykrobe
  - mlst_analyzer.py: MLST analysis using mlst
  - emm_typer.py: emm typing using emmtyper
  - results_analyzer.py: Results filtering and validation
  - report_generator.py: Summary report generation
        """
    )
    
    parser.add_argument("--reads", 
                       help="Tab-separated file with strain IDs and paired read paths")
    parser.add_argument("--contigs", 
                       help="Tab-separated file with strain IDs and contig paths")
    parser.add_argument("--reference-dir", required=True,
                       help="Directory containing reference data")
    parser.add_argument("--output-dir", default="emm1typer_output",
                       help="Output directory for results (default: emm1typer_output)")
    parser.add_argument("--threads", type=int, default=8,
                       help="Number of threads for analysis tools (default: 8)")
    parser.add_argument("--parallel-jobs", type=int, default=10,
                       help="Number of parallel jobs for mykrobe (default: 10)")
    parser.add_argument("--skip-deps-check", action="store_true",
                       help="Skip dependency checking")
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.reads and not args.contigs:
        parser.error("At least one of --reads or --contigs must be provided")
    
    try:
        # Initialize orchestrator
        orchestrator = Emm1TyperOrchestrator(
            reference_dir=args.reference_dir,
            output_dir=args.output_dir,
            threads=args.threads,
            parallel_jobs=args.parallel_jobs
        )
        
        # Check dependencies if requested
        if not args.skip_deps_check:
            orchestrator.check_dependencies()
        
        # Run complete analysis
        orchestrator.run_complete_analysis(
            reads_file=args.reads,
            contigs_file=args.contigs
        )
        
        return 0
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())