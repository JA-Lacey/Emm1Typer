#!/usr/bin/env python3
"""
Emm1typer - Simplified emm1 lineage typing and quality control tool

Main modes:
1. Standard mode: Run mykrobe for lineage typing from reads
2. QC mode: Quality control assessment of assembled contigs
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json
import yaml
import pandas as pd
from scripts.qc_processor import QCProcessor


def run_mykrobe_standard(reads_file, reference_dir, output_dir, threads):
    """Run standard mykrobe analysis on reads"""
    print("Running mykrobe standard analysis...")
    
    # This maintains existing mykrobe functionality
    # Implementation would go here based on your existing mykrobe pipeline
    print(f"Processing reads from {reads_file}")
    print(f"Using reference data from {reference_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Threads: {threads}")
    
    # Placeholder for actual mykrobe implementation
    return True


def run_qc_mode(contigs_file, reference_dir, output_dir, threads):
    """Run QC mode on assembled contigs"""
    print("Running QC mode on assembled contigs...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize QC processor
    qc_processor = QCProcessor(reference_dir, output_dir, threads)
    
    # Run QC analysis
    results = qc_processor.process_contigs(contigs_file)
    
    if results:
        print(f"QC analysis complete! Results saved to {output_dir}/qc_summary.tsv")
        return True
    else:
        print("QC analysis failed")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Emm1typer: emm1 lineage typing and quality control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard mykrobe analysis
  python Emm1typer.py --reads reads.tab --reference-dir ./reference_data
  
  # QC mode for assembled contigs
  python Emm1typer.py --qc --contigs contigs.tab --reference-dir ./reference_data
        """
    )
    
    # Mode selection
    parser.add_argument("--qc", action="store_true", help="Run QC mode on assembled contigs")
    
    # Input files
    parser.add_argument("--reads", help="Tab-separated file with strain IDs and paired read paths")
    parser.add_argument("--contigs", help="Tab-separated file with strain IDs and contig paths")
    
    # Required arguments
    parser.add_argument("--reference-dir", required=True, help="Directory containing reference data")
    
    # Optional arguments
    parser.add_argument("--output-dir", default="emm1typer_output", help="Output directory (default: emm1typer_output)")
    parser.add_argument("--threads", type=int, default=8, help="Number of threads (default: 8)")
    
    args = parser.parse_args()
    
    # Validate input arguments
    if args.qc:
        if not args.contigs:
            parser.error("--qc mode requires --contigs")
        return run_qc_mode(args.contigs, args.reference_dir, args.output_dir, args.threads)
    else:
        if not args.reads:
            parser.error("Standard mode requires --reads")
        return run_mykrobe_standard(args.reads, args.reference_dir, args.output_dir, args.threads)


if __name__ == "__main__":
    sys.exit(main())