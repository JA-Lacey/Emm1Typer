#!/usr/bin/env python3
"""
Report Generator for Emm1typer

Generates comprehensive summary reports from analysis results.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


class ReportGenerator:
    """Generates summary reports from analysis results"""
    
    def __init__(self, output_dir):
        """
        Initialize report generator
        
        Args:
            output_dir: Output directory path
        """
        self.output_dir = Path(output_dir)
    
    def generate_summary_report(self, analysis_summary=None, dependency_versions=None):
        """
        Generate a comprehensive summary report
        
        Args:
            analysis_summary: Dictionary with analysis results (optional)
            dependency_versions: Dictionary with tool versions (optional)
        """
        print("\nGenerating summary report...")
        
        report_file = self.output_dir / "Emm1typer_summary_report.txt"
        
        with open(report_file, 'w') as f:
            f.write("Emm1typer Analysis Summary Report\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Tool versions if available
            if dependency_versions:
                f.write("Tool Versions:\n")
                for tool, version in dependency_versions.items():
                    f.write(f"  {tool}: {version}\n")
                f.write("\n")
            
            # emm1 lineage results
            self._write_lineage_results(f)
            
            # MLST results
            if analysis_summary and 'mlst' in analysis_summary:
                self._write_mlst_results(f, analysis_summary['mlst'])
            else:
                self._write_mlst_results(f)
            
            # emmtyper results
            if analysis_summary and 'emmtyper' in analysis_summary:
                self._write_emmtyper_results(f, analysis_summary['emmtyper'])
            else:
                self._write_emmtyper_results(f)
            
            # Output files summary
            self._write_output_files(f)
        
        print(f"Summary report saved to {report_file}")
    
    def _write_lineage_results(self, file_handle):
        """Write emm1 lineage typing results to report"""
        lineage_file = self.output_dir / "emm1_lineage_results_predictResults.tsv"
        if lineage_file.exists():
            try:
                lineage_df = pd.read_csv(lineage_file, sep='\t')
                file_handle.write(f"emm1 Lineage Typing Results: {len(lineage_df)} samples processed\n")
                
                # Count confidence levels
                if 'confidence' in lineage_df.columns:
                    confidence_counts = lineage_df['confidence'].value_counts()
                    file_handle.write("Confidence distribution:\n")
                    for conf, count in confidence_counts.items():
                        file_handle.write(f"  {conf}: {count}\n")
                file_handle.write("\n")
            except Exception as e:
                file_handle.write(f"emm1 Lineage Typing: Error reading results - {e}\n\n")
        else:
            file_handle.write("emm1 Lineage Typing: No results found\n\n")
    
    def _write_mlst_results(self, file_handle, mlst_analysis=None):
        """Write MLST analysis results to report"""
        mlst_file = self.output_dir / "mlst_results.tsv"
        
        if mlst_file.exists():
            try:
                if mlst_analysis:
                    # Use analysis summary if provided
                    file_handle.write(f"MLST Analysis Results: {mlst_analysis['total_samples']} samples processed\n")
                    file_handle.write(f"Samples with acceptable MLST profiles: {mlst_analysis['acceptable_samples']}\n")
                    file_handle.write(f"Acceptable MLST profiles: {', '.join(mlst_analysis['acceptable_profiles'])}\n")
                    
                    if mlst_analysis['non_acceptable_samples']:
                        file_handle.write("Non-acceptable samples:\n")
                        for sample, st_type in mlst_analysis['non_acceptable_samples']:
                            file_handle.write(f"  {sample}: {st_type}\n")
                else:
                    # Read file directly
                    mlst_df = pd.read_csv(mlst_file, sep='\t', header=None)
                    file_handle.write(f"MLST Analysis Results: {len(mlst_df)} samples processed\n")
                    
                    # Check for acceptable results file
                    acceptable_mlst_file = self.output_dir / "acceptable_mlst_results.tsv"
                    if acceptable_mlst_file.exists():
                        acc_mlst_df = pd.read_csv(acceptable_mlst_file, sep='\t', header=None)
                        file_handle.write(f"Samples with acceptable MLST profiles: {len(acc_mlst_df)}\n")
                
                file_handle.write("\n")
                
            except Exception as e:
                file_handle.write(f"MLST Analysis: Error reading results - {e}\n\n")
        else:
            file_handle.write("MLST Analysis: No results found\n\n")
    
    def _write_emmtyper_results(self, file_handle, emmtyper_analysis=None):
        """Write emmtyper analysis results to report"""
        emmtyper_file = self.output_dir / "emmtyper_results.tsv"
        
        if emmtyper_file.exists():
            try:
                if emmtyper_analysis:
                    # Use analysis summary if provided
                    file_handle.write(f"emmtyper Analysis Results: {emmtyper_analysis['total_samples']} samples processed\n")
                    file_handle.write(f"Samples with acceptable emm types: {emmtyper_analysis['acceptable_samples']}\n")
                    file_handle.write(f"Acceptable emm types: {', '.join(emmtyper_analysis['acceptable_types'])}\n")
                    
                    if emmtyper_analysis['non_acceptable_samples']:
                        file_handle.write("Non-acceptable samples:\n")
                        for sample, emm_type in emmtyper_analysis['non_acceptable_samples']:
                            file_handle.write(f"  {sample}: {emm_type}\n")
                else:
                    # Read file directly
                    emmtyper_df = pd.read_csv(emmtyper_file, sep='\t')
                    file_handle.write(f"emmtyper Analysis Results: {len(emmtyper_df)} samples processed\n")
                    
                    # Check for acceptable results file
                    acceptable_emmtyper_file = self.output_dir / "acceptable_emmtyper_results.tsv"
                    if acceptable_emmtyper_file.exists():
                        acc_emmtyper_df = pd.read_csv(acceptable_emmtyper_file, sep='\t')
                        file_handle.write(f"Samples with acceptable emm types: {len(acc_emmtyper_df)}\n")
                
                file_handle.write("\n")
                
            except Exception as e:
                file_handle.write(f"emmtyper Analysis: Error reading results - {e}\n\n")
        else:
            file_handle.write("emmtyper Analysis: No results found\n\n")
    
    def _write_output_files(self, file_handle):
        """Write list of output files to report"""
        file_handle.write("Output Files:\n")
        
        # List all TSV and JSON files
        output_files = []
        output_files.extend(self.output_dir.glob("*.tsv"))
        output_files.extend(self.output_dir.glob("*.json"))
        output_files.extend(self.output_dir.glob("*.txt"))
        
        for output_file in sorted(output_files):
            file_handle.write(f"  {output_file.name}\n")