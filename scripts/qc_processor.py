#!/usr/bin/env python3
"""
QC Processor for Emm1typer

Handles quality control analysis of assembled contigs including:
- emmtyper analysis
- MLST analysis  
- seqkit assembly statistics
- Comparison against acceptable values
"""

import subprocess
import json
import yaml
import pandas as pd
import shutil
from pathlib import Path


class QCProcessor:
    """Handles quality control analysis of assembled contigs"""
    
    def __init__(self, reference_dir, output_dir, threads=8):
        """
        Initialize QC processor
        
        Args:
            reference_dir: Directory containing reference data and acceptable values
            output_dir: Output directory for results
            threads: Number of threads for analysis tools
        """
        self.reference_dir = Path(reference_dir)
        self.output_dir = Path(output_dir)
        self.threads = threads
        
        # Load acceptable values
        self.acceptable_emm = self._load_acceptable_values('acceptable_emm_types.yaml', 'emm_types')
        self.acceptable_mlst = self._load_acceptable_values('acceptable_mlst_profiles.yaml', 'mlst_profiles')
        self.acceptable_assembly = self._load_acceptable_assembly_metrics()
    
    def _load_acceptable_values(self, filename, key):
        """Load acceptable values from YAML file"""
        try:
            with open(self.reference_dir / filename, 'r') as f:
                data = yaml.safe_load(f)
                return data.get(key, [])
        except Exception as e:
            print(f"Warning: Could not load {filename}: {e}")
            return []
    
    def _load_acceptable_assembly_metrics(self):
        """Load acceptable assembly quality metrics"""
        # Default acceptable assembly metrics
        default_metrics = {
            "min_genome_size": 1800000,  # 1.8 Mb
            "max_genome_size": 2200000,  # 2.2 Mb
            "max_contigs": 100,
            "min_n50": 50000,
            "max_n_content": 5.0  # percentage
        }
        
        # Try to load from JSON file if it exists
        metrics_file = self.reference_dir / 'acceptable_assembly_metrics.json'
        if metrics_file.exists():
            try:
                with open(metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load assembly metrics file: {e}")
        
        return default_metrics
    
    def process_contigs(self, contigs_file):
        """
        Process contigs file and run QC analysis
        
        Args:
            contigs_file: Tab-separated file with columns: Strain_ID, contigs_path
            
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"Processing contigs for QC analysis from {contigs_file}...")
        
        if not Path(contigs_file).exists():
            print(f"Error: Contigs file {contigs_file} not found")
            return False
        
        # Read contigs file
        try:
            contigs_df = pd.read_csv(contigs_file, sep='\t', header=None, names=['Strain_ID', 'contigs_path'])
        except Exception as e:
            print(f"Error reading contigs file: {e}")
            return False
        
        # Initialize results
        results = []
        
        for _, row in contigs_df.iterrows():
            strain_id = row['Strain_ID']
            contigs_path = row['contigs_path']
            
            print(f"Processing strain: {strain_id}")
            
            # Run QC analysis for this strain
            strain_result = self._analyze_strain(strain_id, contigs_path)
            results.append(strain_result)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        return True
    
    def _analyze_strain(self, strain_id, contigs_path):
        """Analyze a single strain"""
        result = {
            'Strain_ID': strain_id,
            'ST': 'Unknown',
            'EMM': 'Unknown', 
            'Lineage': 'Unknown',
            'QC_Status': 'FAIL',
            'Comments': []
        }
        
        if not Path(contigs_path).exists():
            result['Comments'].append(f"Contigs file not found: {contigs_path}")
            return result
        
        # Create temp directory for this strain
        temp_dir = self.output_dir / f"temp_{strain_id}"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # Copy contigs file
            strain_contigs = temp_dir / f"{strain_id}.fa"
            shutil.copy2(contigs_path, strain_contigs)
            
            # Run emmtyper
            emm_result = self._run_emmtyper(strain_contigs)
            result['EMM'] = emm_result
            
            # Run MLST
            mlst_result = self._run_mlst(strain_contigs)
            result['ST'] = mlst_result
            
            # Run seqkit stats
            assembly_stats = self._run_seqkit_stats(strain_contigs)
            
            # Run mykrobe predict to get lineage from final genotype
            mykrobe_lineage = self._run_mykrobe_predict(strain_id, strain_contigs, temp_dir)
            result['Lineage'] = mykrobe_lineage
            
            # Perform QC checks
            qc_status, comments = self._perform_qc_checks(emm_result, mlst_result, assembly_stats)
            result['QC_Status'] = qc_status
            result['Comments'].extend(comments)
            
        except Exception as e:
            result['Comments'].append(f"Analysis error: {str(e)}")
        finally:
            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)
        
        return result
    
    def _run_emmtyper(self, contigs_file):
        """Run emmtyper on contigs"""
        try:
            cmd = ["emmtyper", "--output-format", "verbose", str(contigs_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse emmtyper output - extract EMM type and cluster info
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) > 5:
                        emm_type = parts[3]  # EMM type (e.g., EMM1.0)
                        cluster = parts[5]   # Cluster (e.g., A-C3)
                        return f"{emm_type} {cluster}"
            
            return "Unknown"
            
        except subprocess.CalledProcessError as e:
            print(f"emmtyper failed: {e}")
            return "Failed"
    
    def _run_mlst(self, contigs_file):
        """Run MLST analysis on contigs"""
        try:
            cmd = ["mlst", "--scheme", "spyogenes", str(contigs_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse MLST output
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if line and not line.startswith('#'):
                    parts = line.split('\t')
                    if len(parts) > 2:
                        return parts[2]  # ST is typically in third column
            
            return "Unknown"
            
        except subprocess.CalledProcessError as e:
            print(f"MLST failed: {e}")
            return "Failed"
    
    def _run_seqkit_stats(self, contigs_file):
        """Run seqkit stats on contigs"""
        try:
            cmd = ["seqkit", "stats", "-a", str(contigs_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse seqkit output
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                header = lines[0].split()
                data = lines[1].split()
                
                stats = {}
                for i, col in enumerate(header):
                    if i < len(data):
                        try:
                            if col in ['sum_len', 'min_len', 'avg_len', 'max_len', 'N50']:
                                stats[col] = int(data[i].replace(',', ''))
                            elif col == 'sum_gap':
                                stats[col] = int(data[i].replace(',', ''))
                            elif col == 'num_seqs':
                                stats[col] = int(data[i].replace(',', ''))
                            else:
                                stats[col] = data[i]
                        except:
                            stats[col] = data[i]
                
                return stats
            
            return {}
            
        except subprocess.CalledProcessError as e:
            print(f"seqkit stats failed: {e}")
            return {}
    
    def _run_mykrobe_predict(self, strain_id, contigs_file, temp_dir):
        """Extract lineage from existing mykrobe results or run mykrobe predict if needed"""
        try:
            # First, check if mykrobe results already exist from standard mode
            existing_results = self._check_existing_mykrobe_results(strain_id)
            if existing_results:
                return existing_results
            
            # If no existing results, run mykrobe predict
            return self._run_fresh_mykrobe_predict(strain_id, contigs_file, temp_dir)
            
        except Exception as e:
            print(f"Error getting mykrobe results for {strain_id}: {e}")
            return "Unknown"
    
    def _check_existing_mykrobe_results(self, strain_id):
        """Check if mykrobe results already exist from standard mode and extract lineage"""
        try:
            # Check for existing mykrobe results file from standard mode
            results_file = self.output_dir / "mykrobe_predictResults.tsv"
            
            if results_file.exists():
                # Read existing results
                df = pd.read_csv(results_file, sep='\t')
                
                # Find the row for this strain
                strain_row = df[df['genome'] == strain_id]
                
                if len(strain_row) > 0:
                    final_genotype = strain_row['final genotype'].iloc[0]
                    print(f"Found existing mykrobe result for {strain_id}: {final_genotype}")
                    return final_genotype
            
            # Check for individual JSON files in temp directory (if they weren't cleaned up)
            temp_json = self.output_dir / "temp_mykrobe" / f"{strain_id}_mykrobe.json"
            if temp_json.exists():
                return self._extract_lineage_from_json(temp_json, strain_id)
            
            return None
            
        except Exception as e:
            print(f"Error checking existing mykrobe results for {strain_id}: {e}")
            return None
    
    def _extract_lineage_from_json(self, json_file, strain_id):
        """Extract final genotype from mykrobe JSON file"""
        try:
            with open(json_file, 'r') as f:
                myk_result = json.load(f)
            
            # Extract genome name and phylogenetics data
            genome_name = list(myk_result.keys())[0]
            genome_data = myk_result[genome_name]
            
            if "phylogenetics" in genome_data:
                phylo_data = genome_data["phylogenetics"]
                
                # Check if lineage data exists
                if "lineage" in phylo_data and phylo_data["lineage"]:
                    # Import the existing parser to extract lineage info
                    import sys
                    sys.path.append(str(self.reference_dir.parent / "scripts"))
                    from parse_mykrobe_predict_emm1 import extract_lineage_info
                    
                    # Load alleles mapping
                    lineage_name_dict = {}
                    alleles_file = self.reference_dir / "emm1_alleles.txt"
                    if alleles_file.exists():
                        with open(alleles_file, 'r') as f:
                            for line in f:
                                fields = line.strip().split('\t')
                                if len(fields) >= 4:
                                    lineage_name_dict[fields[2]] = fields[3]
                    
                    # Extract lineage info using existing parser
                    lineage_table = extract_lineage_info(phylo_data, genome_name, lineage_name_dict)
                    
                    # Get final genotype from the parsed result
                    if len(lineage_table) > 0 and 'final genotype' in lineage_table.columns:
                        final_genotype = lineage_table['final genotype'].iloc[0]
                        return final_genotype
            
            return "Unknown"
            
        except Exception as e:
            print(f"Error extracting lineage from JSON for {strain_id}: {e}")
            return "Unknown"
    
    def _run_fresh_mykrobe_predict(self, strain_id, contigs_file, temp_dir):
        """Run fresh mykrobe predict analysis if no existing results found"""
        try:
            print(f"No existing mykrobe results found for {strain_id}, running fresh analysis...")
            
            # Prepare reference files
            probes_file = self.reference_dir / "probes.fa"
            lineage_file = self.reference_dir / "lineage.json"
            
            # Check if reference files exist
            if not probes_file.exists() or not lineage_file.exists():
                print(f"Warning: Missing reference files for mykrobe predict")
                return "Unknown"
            
            output_file = temp_dir / f"{strain_id}_mykrobe.json"
            
            cmd = [
                "mykrobe", "predict",
                "--sample", strain_id,
                "--species", "custom",
                "--seq", str(contigs_file),
                "--custom_lineage_json", str(lineage_file),
                "--custom_probe_set_path", str(probes_file),
                "--format", "json",
                "-o", str(output_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse the fresh mykrobe JSON output
            if output_file.exists():
                return self._extract_lineage_from_json(output_file, strain_id)
            
            return "Unknown"
            
        except subprocess.CalledProcessError as e:
            print(f"mykrobe predict failed for {strain_id}: {e}")
            return "Failed"
    
    def _determine_lineage(self, emm_type, st_type):
        """Determine lineage based on EMM and ST (simplified)"""
        if emm_type.startswith('emm1') and st_type in ['ST28', 'ST15']:
            return 'emm1.0'
        elif emm_type.startswith('emm1'):
            return 'emm1_variant'
        else:
            return 'non-emm1'
    
    def _perform_qc_checks(self, emm_result, mlst_result, assembly_stats):
        """Perform quality control checks"""
        comments = []
        qc_status = "PASS"
        
        # Extract EMM type from full emmtyper output for validation
        emm_type_for_check = self._extract_emm_type_from_result(emm_result)
        
        # Check EMM type with pattern matching for EMM1.* variants
        emm_acceptable = self._is_acceptable_emm_type(emm_type_for_check)
        if not emm_acceptable:
            if emm_type_for_check in ['Unknown', 'Failed']:
                comments.append("EMM typing failed")
            else:
                comments.append(f"EMM type {emm_type_for_check} not acceptable (must be EMM1.* variant)")
            qc_status = "FAIL"
        
        # Check MLST
        if mlst_result not in self.acceptable_mlst:
            if mlst_result in ['Unknown', 'Failed']:
                comments.append("MLST typing failed")
            else:
                comments.append(f"ST {mlst_result} not in acceptable list")
            qc_status = "FAIL"
        
        # Check assembly quality
        if assembly_stats:
            if 'sum_len' in assembly_stats:
                genome_size = assembly_stats['sum_len']
                if genome_size < self.acceptable_assembly['min_genome_size']:
                    comments.append(f"Genome size too small: {genome_size}")
                    qc_status = "FAIL"
                elif genome_size > self.acceptable_assembly['max_genome_size']:
                    comments.append(f"Genome size too large: {genome_size}")
                    qc_status = "FAIL"
            
            if 'num_seqs' in assembly_stats:
                num_contigs = assembly_stats['num_seqs']
                if num_contigs > self.acceptable_assembly['max_contigs']:
                    comments.append(f"Too many contigs: {num_contigs}")
                    qc_status = "FAIL"
            
            if 'N50' in assembly_stats:
                n50 = assembly_stats['N50']
                if n50 < self.acceptable_assembly['min_n50']:
                    comments.append(f"N50 too low: {n50}")
                    qc_status = "FAIL"
        
        if not comments:
            comments.append("All QC checks passed")
        
        return qc_status, comments
    
    def _extract_emm_type_from_result(self, emm_result):
        """Extract just the EMM type from the emmtyper result for validation"""
        if emm_result in ['Unknown', 'Failed']:
            return emm_result
        
        # If it's the formatted "EMM1.0 A-C3" format, extract just the EMM type
        try:
            parts = emm_result.split()
            if len(parts) >= 1:
                return parts[0]  # EMM type is the first part (e.g., "EMM1.0")
            return emm_result
        except:
            return emm_result
    
    def _is_acceptable_emm_type(self, emm_type):
        """
        Check if EMM type is acceptable using pattern matching
        
        Accepts:
        - Exact matches from the acceptable_emm_types list
        - Any EMM1.* variant (case-insensitive)
        - EMM1.* variants with ~ suffix
        """
        if not emm_type or emm_type in ['Unknown', 'Failed']:
            return False
        
        # Check exact matches first
        if emm_type in self.acceptable_emm:
            return True
        
        # Pattern matching for EMM1.* variants
        emm_lower = emm_type.lower()
        
        # Remove ~ if present for pattern matching
        clean_emm = emm_lower.rstrip('~')
        
        # Check if it's an EMM1 variant
        if clean_emm.startswith('emm1.'):
            try:
                # Extract the number after emm1.
                variant_num = clean_emm[5:]  # Remove 'emm1.'
                # Check if it's a valid number
                float(variant_num)
                return True
            except ValueError:
                return False
        
        return False
    
    def _generate_summary_report(self, results):
        """Generate summary report"""
        # Convert to DataFrame
        df_results = pd.DataFrame(results)
        
        # Convert comments list to string
        df_results['Comments'] = df_results['Comments'].apply(lambda x: '; '.join(x))
        
        # Save to TSV
        output_file = self.output_dir / "qc_summary.tsv"
        df_results.to_csv(output_file, sep='\t', index=False)
        
        # Print summary
        total_samples = len(results)
        passed_samples = len([r for r in results if r['QC_Status'] == 'PASS'])
        failed_samples = total_samples - passed_samples
        
        print(f"\nQC Summary:")
        print(f"Total samples: {total_samples}")
        print(f"Passed QC: {passed_samples}")
        print(f"Failed QC: {failed_samples}")
        print(f"Summary saved to: {output_file}")