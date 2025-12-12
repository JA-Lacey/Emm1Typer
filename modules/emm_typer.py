#!/usr/bin/env python3
"""
emm Typer for Emm1typer

Handles emm typing from assembled contigs using emmtyper tool.
"""

import subprocess
import pandas as pd
import shutil
from pathlib import Path


class EmmTyper:
    """Handles emm typing using emmtyper tool"""
    
    def __init__(self, output_dir, threads=8):
        """
        Initialize emm typer
        
        Args:
            output_dir: Output directory path
            threads: Number of threads for emmtyper
        """
        self.output_dir = Path(output_dir)
        self.threads = threads
    
    def process_contigs(self, contigs_file):
        """
        Process contigs using emmtyper
        
        Args:
            contigs_file: Tab-separated file with columns: Strain_ID, contigs_path
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Processing contigs for emmtyping from {contigs_file}...")
        
        if not Path(contigs_file).exists():
            print(f"Error: Contigs file {contigs_file} not found")
            return False
        
        # Read contigs file
        try:
            contigs_df = pd.read_csv(contigs_file, sep='\t', header=None, names=['Strain_ID', 'contigs_path'])
        except Exception as e:
            print(f"Error reading contigs file: {e}")
            return False
        
        # Create temporary directory for contigs
        temp_dir = self.output_dir / "temp_contigs_emm"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Copy and rename contigs files using shared utility
            from .config_manager import ConfigManager
            contig_files = ConfigManager.prepare_contig_files(contigs_df, temp_dir)
            
            if not contig_files:
                print("No valid contig files found for emmtyping")
                return False
            
            # Run emmtyper
            return self._run_emmtyper(temp_dir)
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _run_emmtyper(self, contigs_dir):
        """Run emmtyper analysis on contigs"""
        print("Running emmtyper analysis...")
        
        emmtyper_cmd = [
            "emmtyper",
            "--threads", str(self.threads),
            "--output-format", "verbose"
        ] + [str(f) for f in contigs_dir.glob("*.fa")]
        
        try:
            result = subprocess.run(emmtyper_cmd, capture_output=True, text=True, check=True)
            
            # Save emmtyper output
            with open(self.output_dir / "emmtyper_results.tsv", 'w') as f:
                f.write(result.stdout)
            
            print(f"emmtyper results saved to {self.output_dir}/emmtyper_results.tsv")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running emmtyper: {e}")
            return False
    
    def get_results_file(self):
        """Get path to emmtyper results file"""
        return self.output_dir / "emmtyper_results.tsv"