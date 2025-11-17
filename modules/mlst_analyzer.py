#!/usr/bin/env python3
"""
MLST Analyzer for Emm1typer

Handles MLST typing from assembled contigs using mlst tool.
"""

import subprocess
import pandas as pd
import shutil
from pathlib import Path


class MLSTAnalyzer:
    """Handles MLST analysis using mlst tool"""
    
    def __init__(self, output_dir, threads=8):
        """
        Initialize MLST analyzer
        
        Args:
            output_dir: Output directory path
            threads: Number of threads for mlst
        """
        self.output_dir = Path(output_dir)
        self.threads = threads
    
    def process_contigs(self, contigs_file):
        """
        Process contigs using MLST
        
        Args:
            contigs_file: Tab-separated file with columns: Strain_ID, contigs_path
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Processing contigs for MLST from {contigs_file}...")
        
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
        temp_dir = self.output_dir / "temp_contigs_mlst"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Copy and rename contigs files
            contig_files = self._prepare_contig_files(contigs_df, temp_dir)
            
            if not contig_files:
                print("No valid contig files found for MLST")
                return False
            
            # Run MLST
            return self._run_mlst(temp_dir)
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _prepare_contig_files(self, contigs_df, temp_dir):
        """Copy and rename contigs files for MLST analysis"""
        contig_files = []
        
        for _, row in contigs_df.iterrows():
            strain_id = row['Strain_ID']
            contig_path = Path(row['contigs_path'])
            
            if not contig_path.exists():
                print(f"Warning: Contigs file {contig_path} not found for strain {strain_id}")
                continue
            
            # Copy to temp directory with strain ID as filename
            dest_file = temp_dir / f"{strain_id}.fa"
            shutil.copy2(contig_path, dest_file)
            contig_files.append(dest_file)
        
        return contig_files
    
    def _run_mlst(self, contigs_dir):
        """Run MLST analysis on contigs"""
        print("Running MLST analysis...")
        
        mlst_cmd = [
            "mlst",
            "--threads", str(self.threads),
            "--scheme", "spyogenes",
            "--json", str(self.output_dir / "mlst_results.json")
        ] + [str(f) for f in contigs_dir.glob("*.fa")]
        
        try:
            result = subprocess.run(mlst_cmd, capture_output=True, text=True, check=True)
            
            # Also save tabular output
            with open(self.output_dir / "mlst_results.tsv", 'w') as f:
                f.write(result.stdout)
            
            print(f"MLST results saved to {self.output_dir}/mlst_results.tsv")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error running MLST: {e}")
            return False
    
    def get_results_files(self):
        """Get paths to MLST results files"""
        return {
            'tsv': self.output_dir / "mlst_results.tsv",
            'json': self.output_dir / "mlst_results.json"
        }