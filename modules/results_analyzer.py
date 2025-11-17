#!/usr/bin/env python3
"""
Results Analyzer for Emm1typer

Handles analysis and filtering of results against acceptable types.
"""

import pandas as pd
from pathlib import Path


class ResultsAnalyzer:
    """Analyzes and filters results against acceptable types"""
    
    def __init__(self, config_manager, output_dir):
        """
        Initialize results analyzer
        
        Args:
            config_manager: ConfigManager instance
            output_dir: Output directory path
        """
        self.config = config_manager
        self.output_dir = Path(output_dir)
        
        # Get acceptable types
        acceptable_types = self.config.get_acceptable_types()
        self.acceptable_emm_types = acceptable_types['emm_types']
        self.acceptable_mlst_profiles = acceptable_types['mlst_profiles']
    
    def analyze_mlst_results(self, mlst_results_file=None):
        """
        Analyze MLST results and check for acceptable profiles
        
        Args:
            mlst_results_file: Path to MLST results file (optional)
            
        Returns:
            dict: Analysis results with counts and warnings
        """
        if mlst_results_file is None:
            mlst_results_file = self.output_dir / "mlst_results.tsv"
        
        if not mlst_results_file.exists():
            print("No MLST results file found")
            return {}
        
        try:
            # Read MLST results
            mlst_df = pd.read_csv(mlst_results_file, sep='\t', header=None)
            
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
            
            # Save acceptable results
            if acceptable_results:
                acceptable_df = pd.DataFrame(acceptable_results)
                acceptable_output = self.output_dir / "acceptable_mlst_results.tsv"
                acceptable_df.to_csv(acceptable_output, sep='\t', index=False, header=False)
                print(f"✓ Found {len(acceptable_results)} samples with acceptable MLST profiles")
            else:
                print("⚠️  No samples found with acceptable MLST profiles")
            
            return {
                'total_samples': len(mlst_df),
                'acceptable_samples': len(acceptable_results),
                'non_acceptable_samples': non_acceptable_samples,
                'acceptable_profiles': self.acceptable_mlst_profiles
            }
                
        except Exception as e:
            print(f"Error analyzing MLST results: {e}")
            return {}
    
    def analyze_emmtyper_results(self, emmtyper_results_file=None):
        """
        Analyze emmtyper results and check for acceptable emm types
        
        Args:
            emmtyper_results_file: Path to emmtyper results file (optional)
            
        Returns:
            dict: Analysis results with counts and warnings
        """
        if emmtyper_results_file is None:
            emmtyper_results_file = self.output_dir / "emmtyper_results.tsv"
        
        if not emmtyper_results_file.exists():
            print("No emmtyper results file found")
            return {}
        
        try:
            # Read emmtyper results
            emmtyper_df = pd.read_csv(emmtyper_results_file, sep='\t')
            
            # Filter for acceptable emm types and collect warnings
            non_acceptable_samples = []
            acceptable_results = pd.DataFrame()
            
            if 'emm_type' in emmtyper_df.columns:
                acceptable_results = emmtyper_df[
                    emmtyper_df['emm_type'].isin(self.acceptable_emm_types)
                ]
                
                # Identify non-acceptable samples
                non_acceptable_df = emmtyper_df[
                    ~emmtyper_df['emm_type'].isin(self.acceptable_emm_types)
                ]
                
                # Collect non-acceptable samples
                for _, row in non_acceptable_df.iterrows():
                    sample_name = row.get('isolate', row.get('sample', 'unknown'))
                    emm_type = row['emm_type']
                    non_acceptable_samples.append((sample_name, emm_type))
                
                # Print warnings for non-acceptable samples
                if not non_acceptable_df.empty:
                    print("\n⚠️  WARNING: Samples with non-acceptable emm types:")
                    for sample_name, emm_type in non_acceptable_samples:
                        print(f"   - {sample_name}: {emm_type} (not in acceptable list)")
                    print(f"   Acceptable emm types: {', '.join(self.acceptable_emm_types)}")
                
                # Save acceptable results
                if not acceptable_results.empty:
                    acceptable_output = self.output_dir / "acceptable_emmtyper_results.tsv"
                    acceptable_results.to_csv(acceptable_output, sep='\t', index=False)
                    print(f"✓ Found {len(acceptable_results)} samples with acceptable emm types")
                else:
                    print("⚠️  No samples found with acceptable emm types")
            else:
                print("Warning: emmtyper results do not contain expected 'emm_type' column")
            
            return {
                'total_samples': len(emmtyper_df),
                'acceptable_samples': len(acceptable_results),
                'non_acceptable_samples': non_acceptable_samples,
                'acceptable_types': self.acceptable_emm_types
            }
                
        except Exception as e:
            print(f"Error analyzing emmtyper results: {e}")
            return {}
    
    def get_analysis_summary(self):
        """Get comprehensive analysis summary"""
        summary = {}
        
        # Analyze MLST results
        mlst_analysis = self.analyze_mlst_results()
        summary['mlst'] = mlst_analysis
        
        # Analyze emmtyper results
        emmtyper_analysis = self.analyze_emmtyper_results()
        summary['emmtyper'] = emmtyper_analysis
        
        return summary