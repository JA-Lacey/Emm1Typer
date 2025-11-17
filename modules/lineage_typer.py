#!/usr/bin/env python3
"""
Lineage Typer for Emm1typer

Handles emm1 lineage typing using mykrobe for paired-end reads.
"""

import subprocess
import shutil
from pathlib import Path


class LineageTyper:
    """Handles emm1 lineage typing using mykrobe"""
    
    def __init__(self, config_manager, output_dir, parallel_jobs=10):
        """
        Initialize lineage typer
        
        Args:
            config_manager: ConfigManager instance
            output_dir: Output directory path
            parallel_jobs: Number of parallel jobs for mykrobe
        """
        self.config = config_manager
        self.output_dir = Path(output_dir)
        self.parallel_jobs = parallel_jobs
        
        # Get reference paths
        ref_paths = self.config.get_reference_paths()
        self.lineage_json = ref_paths['lineage_json']
        self.probes_fa = ref_paths['probes_fa']
        self.emm1_alleles = ref_paths['emm1_alleles']
        self.parse_script = ref_paths['parse_script']
    
    def process_reads(self, reads_file):
        """
        Process reads using mykrobe for emm1 lineage typing
        
        Args:
            reads_file: Tab-separated file with columns: Strain_ID, reads1_path, reads2_path
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Processing reads from {reads_file}...")
        
        if not Path(reads_file).exists():
            print(f"Error: Reads file {reads_file} not found")
            return False
        
        # Create temporary directory for mykrobe outputs
        temp_dir = self.output_dir / "temp_mykrobe"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Run mykrobe predict in parallel
            if not self._run_mykrobe_parallel(reads_file, temp_dir):
                return False
            
            # Process JSON outputs
            if not self._process_mykrobe_outputs(temp_dir):
                return False
            
            print(f"emm1 lineage typing results saved to {self.output_dir}/emm1_lineage_results_predictResults.tsv")
            return True
            
        finally:
            # Clean up temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def _run_mykrobe_parallel(self, reads_file, temp_dir):
        """Run mykrobe predict in parallel using GNU parallel"""
        mykrobe_cmd = (
            f"cat {reads_file} | parallel -j {self.parallel_jobs} --colsep '\\t' "
            f"'mykrobe predict --sample {{1}} --species custom --seq {{2}} {{3}} "
            f"--custom_lineage_json {self.lineage_json} "
            f"--custom_probe_set_path {self.probes_fa} "
            f"--format json -o {temp_dir}/{{1}}.json'"
        )
        
        print("Running mykrobe predict for emm1 lineage typing...")
        try:
            subprocess.run(mykrobe_cmd, shell=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error running mykrobe: {e}")
            return False
    
    def _process_mykrobe_outputs(self, temp_dir):
        """Process mykrobe JSON outputs using the parsing script"""
        json_files = list(temp_dir.glob("*.json"))
        if not json_files:
            print("No mykrobe JSON outputs found")
            return False
        
        print("Processing mykrobe JSON outputs...")
        parse_cmd = [
            "python3", str(self.parse_script),
            "--jsons"] + [str(f) for f in json_files] + [
            "--alleles", str(self.emm1_alleles),
            "--prefix", str(self.output_dir / "emm1_lineage_results")
        ]
        
        try:
            subprocess.run(parse_cmd, check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error processing mykrobe outputs: {e}")
            return False
    
    def get_results_file(self):
        """Get path to the lineage results file"""
        return self.output_dir / "emm1_lineage_results_predictResults.tsv"