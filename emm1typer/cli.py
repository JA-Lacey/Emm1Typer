#!/usr/bin/env python3
"""
Emm1typer - Simplified emm1 lineage typing and quality control tool

Main modes:
1. Standard mode: Run mykrobe for lineage typing from reads
2. QC mode: Quality control assessment of assembled contigs
3. Combined mode: Run both standard and QC modes when both inputs provided
"""

import sys
import argparse
import subprocess
from pathlib import Path
import json
import pandas as pd
from emm1typer.qc_processor import QCProcessor
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import __version__


def run_mykrobe_standard(reads_file, reference_dir, output_dir, threads):
    """Run standard mykrobe analysis on reads with parallel processing"""
    print("Running mykrobe standard analysis...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if not Path(reads_file).exists():
        print(f"Error: Reads file {reads_file} not found")
        return False
    
    # Read reads file
    try:
        reads_df = pd.read_csv(reads_file, sep='\t', header=None, names=['Strain_ID', 'Read1', 'Read2'])
        print(f"Processing {len(reads_df)} strains from {reads_file} using {threads} threads...")
    except Exception as e:
        print(f"Error reading reads file: {e}")
        return False
    
    # Prepare reference files
    reference_path = Path(reference_dir)
    probes_file = reference_path / "probes.fa"
    probes_ref_file = reference_path / "probes.ref.fa"
    if probes_ref_file.exists():
        probes_file = probes_ref_file
    
    lineage_file = reference_path / "lineage.json"
    alleles_file = reference_path / "emm1_alleles.txt"
    
    # Check required reference files
    required_files = [probes_file, lineage_file, alleles_file]
    for req_file in required_files:
        if not req_file.exists():
            print(f"Error: Required reference file not found: {req_file}")
            return False
    
    # Create temporary directory for mykrobe outputs
    temp_dir = output_path / "temp_mykrobe"
    temp_dir.mkdir(exist_ok=True)
    
    json_files = []
    failed_strains = []
    
    try:
        # Process strains in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=threads) as executor:
            # Submit all mykrobe predict tasks
            future_to_strain = {}
            
            for _, row in reads_df.iterrows():
                strain_id = row['Strain_ID']
                read1 = row['Read1']
                read2 = row['Read2']
                
                # Check if read files exist
                if not Path(read1).exists() or not Path(read2).exists():
                    print(f"Warning: Read files not found for strain {strain_id}")
                    failed_strains.append(strain_id)
                    continue
                
                json_output = temp_dir / f"{strain_id}_mykrobe.json"
                
                # Submit mykrobe predict task
                future = executor.submit(_run_mykrobe_predict, strain_id, read1, read2, 
                                       probes_file, lineage_file, json_output, 1)  # Use 1 thread per job since we're parallelizing at strain level
                future_to_strain[future] = (strain_id, json_output)
            
            # Collect results as they complete
            for future in as_completed(future_to_strain):
                strain_id, json_output = future_to_strain[future]
                try:
                    success = future.result()
                    if success:
                        json_files.append(json_output)
                        print(f"Completed mykrobe analysis for strain: {strain_id}")
                    else:
                        failed_strains.append(strain_id)
                        print(f"Failed mykrobe analysis for strain: {strain_id}")
                except Exception as e:
                    print(f"Error processing strain {strain_id}: {e}")
                    failed_strains.append(strain_id)
        
        if not json_files:
            print("Error: No successful mykrobe analyses")
            return False
        
        # Parse mykrobe results
        print("Parsing mykrobe results...")
        success = _parse_mykrobe_results(json_files, alleles_file, output_path)
        
        if success:
            print(f"Standard analysis complete! Results saved to {output_dir}/mykrobe_predictResults.tsv")
            
            if failed_strains:
                print(f"Failed strains: {', '.join(failed_strains)}")
            
            return True
        else:
            print("Failed to parse mykrobe results")
            return False
            
    finally:
        # Clean up temporary files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)


def _run_mykrobe_predict(strain_id, read1, read2, probes_file, lineage_file, json_output, threads):
    """Run mykrobe predict for a single strain"""
    try:
        cmd = [
            "mykrobe", "predict",
            "--sample", strain_id,
            "--species", "custom",
            "--seq", str(read1), str(read2),
            "--custom_lineage_json", str(lineage_file),
            "--custom_probe_set_path", str(probes_file),
            "--format", "json",
            "-o", str(json_output)
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"mykrobe predict failed for {strain_id}: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if e.stdout:
            print(f"Standard output: {e.stdout}")
        return False


def _parse_mykrobe_results(json_files, alleles_file, output_dir):
    """Parse mykrobe JSON results using the existing parser"""
    try:
        # Import the parser
        from emm1typer.parse_mykrobe_predict_emm1 import extract_lineage_info
        import pandas as pd
        
        # Load alleles mapping
        lineage_name_dict = {}
        with open(alleles_file, 'r') as f:
            for line in f:
                fields = line.strip().split('\t')
                if len(fields) >= 4:
                    lineage_name_dict[fields[2]] = fields[3]
        
        results_tables = []
        
        # Process each JSON file
        for json_file in json_files:
            with open(json_file) as f:
                myk_result = json.load(f)
            
            if len(list(myk_result.keys())) > 1:
                print(f"Warning: More than one result in {json_file}")
                continue
            
            genome_name = list(myk_result.keys())[0]
            genome_data = myk_result[genome_name]
            lineage_data = genome_data["phylogenetics"]
            lineage_table = extract_lineage_info(lineage_data, genome_name, lineage_name_dict)
            results_tables.append(lineage_table)
        
        if results_tables:
            # Combine results
            final_results = pd.concat(results_tables, sort=True)
            
            # Save results
            output_file = output_dir / "mykrobe_predictResults.tsv"
            final_results.to_csv(output_file, index=False, sep="\t", 
                                columns=["genome", "final genotype", "name", 
                                        "confidence", "lowest support for genotype marker", 
                                        "poorly supported markers", "max support for additional markers", 
                                        "additional markers", "node support"])
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error parsing mykrobe results: {e}")
        return False


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


def run_combined_mode(reads_file, contigs_file, reference_dir, output_dir, threads):
    """Run both standard mykrobe and QC modes"""
    print("Running combined mode: Standard mykrobe analysis + QC mode...")
    
    success = True
    
    # Run standard mykrobe analysis
    print("\n=== Running Standard Mode (mykrobe analysis) ===")
    mykrobe_success = run_mykrobe_standard(reads_file, reference_dir, output_dir, threads)
    if not mykrobe_success:
        print("Standard mykrobe analysis failed")
        success = False
    
    # Run QC analysis
    print("\n=== Running QC Mode (contig quality control) ===")
    qc_success = run_qc_mode(contigs_file, reference_dir, output_dir, threads)
    if not qc_success:
        print("QC analysis failed")
        success = False
    
    # Summary
    if success:
        print("\n=== Combined Analysis Complete ===")
        print(f"✓ Standard mykrobe analysis: {'SUCCESS' if mykrobe_success else 'FAILED'}")
        print(f"✓ QC analysis: {'SUCCESS' if qc_success else 'FAILED'}")
        print(f"Results saved to {output_dir}/")
    
    return success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Emm1typer: emm1 lineage typing and quality control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard mykrobe analysis only
  emm1typer --reads reads.tab --reference-dir ./reference_data
  
  # QC mode only
  emm1typer --qc --contigs contigs.tab --reference-dir ./reference_data
  
  # Combined mode (both standard and QC)
  emm1typer --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data
  
  # Combined mode with explicit QC flag (same as above)
  emm1typer --qc --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data
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
    
    # Version
    parser.add_argument("--version", action="version", version=f"emm1typer {__version__}")
    
    args = parser.parse_args()
    
    # Validate input arguments and determine mode
    if args.reads and args.contigs:
        # Combined mode: both standard and QC
        print("Both reads and contigs provided - running combined mode")
        return run_combined_mode(args.reads, args.contigs, args.reference_dir, args.output_dir, args.threads)
    
    elif args.qc and args.contigs:
        # QC mode only
        return run_qc_mode(args.contigs, args.reference_dir, args.output_dir, args.threads)
    
    elif args.reads and not args.qc:
        # Standard mode only
        return run_mykrobe_standard(args.reads, args.reference_dir, args.output_dir, args.threads)
    
    else:
        # Invalid combinations
        if args.qc and not args.contigs:
            parser.error("--qc mode requires --contigs")
        elif not args.reads and not args.contigs:
            parser.error("At least one of --reads or --contigs must be provided")
        else:
            parser.error("Invalid combination of arguments")


if __name__ == "__main__":
    sys.exit(main())
