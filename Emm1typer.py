#!/usr/bin/env python3
"""
Emm1typer.py - Comprehensive emm1 lineage typing, MLST, and emmtyping analysis

This script processes both reads and contigs to perform:
1. emm1 lineage typing using mykrobe for reads
2. MLST typing using mlst for contigs
3. emmtyping using emmtyper for contigs

Author: Generated for genomic implementation
Date: November 2025
"""

import argparse
import os
import sys
import subprocess
import json
import pandas as pd
import yaml
import concurrent.futures
from pathlib import Path
import tempfile
import shutil

class Emm1Typer:
    def __init__(self, reference_dir, output_dir="output", threads=8, parallel_jobs=10):
        """
        Initialize Emm1Typer with reference data paths
        
        Args:
            reference_dir: Path to reference data directory
            output_dir: Output directory for results
            threads: Number of threads for analysis tools
            parallel_jobs: Number of parallel jobs for mykrobe
        """
        self.reference_dir = Path(reference_dir)
        self.output_dir = Path(output_dir)
        self.threads = threads
        self.parallel_jobs = parallel_jobs
        
        # Reference files
        self.lineage_json = self.reference_dir / "lineage.json"
        self.probes_fa = self.reference_dir / "probes.fa"
        self.emm1_alleles = self.reference_dir / "emm1_alleles.txt"
        self.emm_types_yaml = self.reference_dir / "acceptable_emm_types.yaml"
        self.mlst_profiles_yaml = self.reference_dir / "acceptable_mlst_profiles.yaml"
        self.parse_script = Path(__file__).parent / "scripts" / "parse_mykrobe_predict_emm1.py"
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load acceptable types from YAML files
        self.acceptable_emm_types = self._load_acceptable_types()
        self.acceptable_mlst_profiles = self._load_acceptable_mlst()
        
        # Validate reference files
        self._validate_references()
    
    def _load_acceptable_types(self):
        """Load acceptable emm types from YAML file"""
        try:
            with open(self.emm_types_yaml, 'r') as f:
                data = yaml.safe_load(f)
                return data['emm_types']
        except Exception as e:
            print(f"Error loading acceptable emm types from {self.emm_types_yaml}: {e}")
            # Fallback to hardcoded list
            return [f"emm1.{i}" for i in range(20)]
    
    def _load_acceptable_mlst(self):
        """Load acceptable MLST profiles from YAML file"""
        try:
            with open(self.mlst_profiles_yaml, 'r') as f:
                data = yaml.safe_load(f)
                return data['mlst_profiles']
        except Exception as e:
            print(f"Error loading acceptable MLST profiles from {self.mlst_profiles_yaml}: {e}")
            # Fallback to hardcoded list
            return ["ST28", "ST15", "ST101", "ST334", "ST403"]
    
    def _validate_references(self):
        """Validate that all required reference files exist"""
        required_files = [
            self.lineage_json, 
            self.probes_fa, 
            self.emm1_alleles, 
            self.parse_script,
            self.emm_types_yaml,
            self.mlst_profiles_yaml
        ]
        missing_files = [f for f in required_files if not f.exists()]
        
        if missing_files:
            print(f"Error: Missing required reference files:")
            for f in missing_files:
                print(f"  - {f}")
            sys.exit(1)
    
    def _check_dependencies(self):
        """Check if required external tools are available"""
        required_tools = ['mykrobe', 'mlst', 'emmtyper', 'parallel']
        missing_tools = []
        
        for tool in required_tools:
            try:
                subprocess.run([tool, '--help'], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"Error: Missing required tools: {', '.join(missing_tools)}")
            print("Please install the missing tools before running this script.")
            sys.exit(1)
    
    def process_reads(self, reads_file):
        """
        Process reads using mykrobe for emm1 lineage typing
        
        Args:
            reads_file: Tab-separated file with columns: Strain_ID, reads1_path, reads2_path
        """
        print(f"Processing reads from {reads_file}...")
        
        if not Path(reads_file).exists():
            print(f"Error: Reads file {reads_file} not found")
            return
        
        # Create temporary directory for mykrobe outputs
        temp_dir = self.output_dir / "temp_mykrobe"
        temp_dir.mkdir(exist_ok=True)
        
        # Run mykrobe predict in parallel using GNU parallel
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
        except subprocess.CalledProcessError as e:
            print(f"Error running mykrobe: {e}")
            return
        
        # Process JSON outputs
        json_files = list(temp_dir.glob("*.json"))
        if not json_files:
            print("No mykrobe JSON outputs found")
            return
        
        print("Processing mykrobe JSON outputs...")
        parse_cmd = [
            "python3", str(self.parse_script),
            "--jsons"] + [str(f) for f in json_files] + [
            "--alleles", str(self.emm1_alleles),
            "--prefix", str(self.output_dir / "emm1_lineage_results")
        ]
        
        try:
            subprocess.run(parse_cmd, check=True)
            print(f"emm1 lineage typing results saved to {self.output_dir}/emm1_lineage_results_predictResults.tsv")
        except subprocess.CalledProcessError as e:
            print(f"Error processing mykrobe outputs: {e}")
        
        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def process_contigs(self, contigs_file):
        """
        Process contigs using MLST and emmtyper
        
        Args:
            contigs_file: Tab-separated file with columns: Strain_ID, contigs_path
        """
        print(f"Processing contigs from {contigs_file}...")
        
        if not Path(contigs_file).exists():
            print(f"Error: Contigs file {contigs_file} not found")
            return
        
        # Read contigs file
        contigs_df = pd.read_csv(contigs_file, sep='\t', header=None, names=['Strain_ID', 'contigs_path'])
        
        # Create temporary directory for contigs
        temp_dir = self.output_dir / "temp_contigs"
        temp_dir.mkdir(exist_ok=True)
        
        # Copy and rename contigs files
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
        
        if not contig_files:
            print("No valid contig files found")
            return
        
        # Run MLST
        self._run_mlst(temp_dir)
        
        # Run emmtyper
        self._run_emmtyper(temp_dir)
        
        # Clean up temporary files
        shutil.rmtree(temp_dir, ignore_errors=True)
    
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
            self._analyze_mlst_results()
            
        except subprocess.CalledProcessError as e:
            print(f"Error running MLST: {e}")
    
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
            self._analyze_emmtyper_results()
            
        except subprocess.CalledProcessError as e:
            print(f"Error running emmtyper: {e}")
    
    def _analyze_mlst_results(self):
        """Analyze MLST results and check for acceptable profiles"""
        try:
            mlst_file = self.output_dir / "mlst_results.tsv"
            if not mlst_file.exists():
                return
            
            # Read MLST results
            mlst_df = pd.read_csv(mlst_file, sep='\t', header=None)
            
            # Filter for acceptable MLST profiles and collect warnings
            acceptable_results = []
            non_acceptable_samples = []
            
            for _, row in mlst_df.iterrows():
                if len(row) >= 2:  # Check if we have at least filename and ST columns
                    sample_name = str(row[0]).split('.')[0] if pd.notna(row[0]) else "unknown"
                    st_type = str(row[1]) if pd.notna(row[1]) else "unknown"
                    
                    if st_type in self.acceptable_mlst_profiles:
                        acceptable_results.append(row)
                    else:
                        non_acceptable_samples.append((sample_name, st_type))
            
            # Print warnings for non-acceptable samples
            if non_acceptable_samples:
                print("\n⚠️  WARNING: Samples with non-acceptable MLST profiles:")
                for sample, st_type in non_acceptable_samples:
                    print(f"   - {sample}: {st_type} (not in acceptable list)")
                print(f"   Acceptable MLST profiles: {', '.join(self.acceptable_mlst_profiles)}")
            
            if acceptable_results:
                acceptable_df = pd.DataFrame(acceptable_results)
                acceptable_df.to_csv(self.output_dir / "acceptable_mlst_results.tsv", 
                                   sep='\t', index=False, header=False)
                print(f"✓ Found {len(acceptable_results)} samples with acceptable MLST profiles")
            else:
                print("⚠️  No samples found with acceptable MLST profiles")
                
        except Exception as e:
            print(f"Error analyzing MLST results: {e}")
    
    def _analyze_emmtyper_results(self):
        """Analyze emmtyper results and check for acceptable emm types"""
        try:
            emmtyper_file = self.output_dir / "emmtyper_results.tsv"
            if not emmtyper_file.exists():
                return
            
            # Read emmtyper results
            emmtyper_df = pd.read_csv(emmtyper_file, sep='\t')
            
            # Filter for acceptable emm types and collect warnings
            non_acceptable_samples = []
            
            if 'emm_type' in emmtyper_df.columns:
                acceptable_results = emmtyper_df[
                    emmtyper_df['emm_type'].isin(self.acceptable_emm_types)
                ]
                
                # Identify non-acceptable samples
                non_acceptable_df = emmtyper_df[
                    ~emmtyper_df['emm_type'].isin(self.acceptable_emm_types)
                ]
                
                # Print warnings for non-acceptable samples
                if not non_acceptable_df.empty:
                    print("\n⚠️  WARNING: Samples with non-acceptable emm types:")
                    for _, row in non_acceptable_df.iterrows():
                        sample_name = row.get('isolate', row.get('sample', 'unknown'))
                        emm_type = row['emm_type']
                        print(f"   - {sample_name}: {emm_type} (not in acceptable list)")
                    print(f"   Acceptable emm types: {', '.join(self.acceptable_emm_types)}")
                
                if not acceptable_results.empty:
                    acceptable_results.to_csv(self.output_dir / "acceptable_emmtyper_results.tsv", 
                                            sep='\t', index=False)
                    print(f"✓ Found {len(acceptable_results)} samples with acceptable emm types")
                else:
                    print("⚠️  No samples found with acceptable emm types")
            else:
                print("Warning: emmtyper results do not contain expected 'emm_type' column")
                
        except Exception as e:
            print(f"Error analyzing emmtyper results: {e}")
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\nGenerating summary report...")
        
        report_file = self.output_dir / "Emm1typer_summary_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("Emm1typer Analysis Summary Report\n")
            f.write("=" * 50 + "\n\n")
            
            # emm1 lineage results
            lineage_file = self.output_dir / "emm1_lineage_results_predictResults.tsv"
            if lineage_file.exists():
                lineage_df = pd.read_csv(lineage_file, sep='\t')
                f.write(f"emm1 Lineage Typing Results: {len(lineage_df)} samples processed\n")
                
                # Count confidence levels
                if 'confidence' in lineage_df.columns:
                    confidence_counts = lineage_df['confidence'].value_counts()
                    f.write("Confidence distribution:\n")
                    for conf, count in confidence_counts.items():
                        f.write(f"  {conf}: {count}\n")
                f.write("\n")
            
            # MLST results
            mlst_file = self.output_dir / "mlst_results.tsv"
            acceptable_mlst_file = self.output_dir / "acceptable_mlst_results.tsv"
            
            if mlst_file.exists():
                mlst_df = pd.read_csv(mlst_file, sep='\t', header=None)
                f.write(f"MLST Analysis Results: {len(mlst_df)} samples processed\n")
                
                if acceptable_mlst_file.exists():
                    acc_mlst_df = pd.read_csv(acceptable_mlst_file, sep='\t', header=None)
                    f.write(f"Samples with acceptable MLST profiles: {len(acc_mlst_df)}\n")
                f.write(f"Acceptable MLST profiles: {', '.join(self.acceptable_mlst_profiles)}\n\n")
            
            # emmtyper results
            emmtyper_file = self.output_dir / "emmtyper_results.tsv"
            acceptable_emmtyper_file = self.output_dir / "acceptable_emmtyper_results.tsv"
            
            if emmtyper_file.exists():
                emmtyper_df = pd.read_csv(emmtyper_file, sep='\t')
                f.write(f"emmtyper Analysis Results: {len(emmtyper_df)} samples processed\n")
                
                if acceptable_emmtyper_file.exists():
                    acc_emmtyper_df = pd.read_csv(acceptable_emmtyper_file, sep='\t')
                    f.write(f"Samples with acceptable emm types: {len(acc_emmtyper_df)}\n")
                f.write(f"Acceptable emm types: {', '.join(self.acceptable_emm_types)}\n\n")
            
            f.write("Output Files:\n")
            for output_file in self.output_dir.glob("*.tsv"):
                f.write(f"  {output_file.name}\n")
            for output_file in self.output_dir.glob("*.json"):
                f.write(f"  {output_file.name}\n")
        
        print(f"Summary report saved to {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Emm1typer: Comprehensive emm1 lineage typing, MLST, and emmtyping analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process reads only
  python Emm1typer.py --reads reads.tab --reference-dir ./reference_data

  # Process contigs only  
  python Emm1typer.py --contigs contigs.tab --reference-dir ./reference_data

  # Process both reads and contigs
  python Emm1typer.py --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data

Input file formats:
  reads.tab: Strain_ID<tab>reads1_path<tab>reads2_path
  contigs.tab: Strain_ID<tab>contigs_path
        """
    )
    
    parser.add_argument("--reads", 
                       help="Tab-separated file with strain IDs and paired read paths")
    parser.add_argument("--contigs", 
                       help="Tab-separated file with strain IDs and contig paths")
    parser.add_argument("--reference-dir", required=True,
                       help="Directory containing reference data (lineage.json, probes.fa, emm1_alleles.txt)")
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
    
    # Initialize Emm1Typer
    try:
        typer = Emm1Typer(
            reference_dir=args.reference_dir,
            output_dir=args.output_dir,
            threads=args.threads,
            parallel_jobs=args.parallel_jobs
        )
    except SystemExit:
        return 1
    
    # Check dependencies
    if not args.skip_deps_check:
        typer._check_dependencies()
    
    # Process reads if provided
    if args.reads:
        typer.process_reads(args.reads)
    
    # Process contigs if provided
    if args.contigs:
        typer.process_contigs(args.contigs)
    
    # Generate summary report
    typer.generate_summary_report()
    
    print(f"\nAnalysis complete! Results saved to {args.output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())