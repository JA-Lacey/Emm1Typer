#!/usr/bin/env python3
"""
Configuration Manager for Emm1typer

Handles loading and validation of reference data and configuration files.
"""

import sys
import yaml
from pathlib import Path


class ConfigManager:
    """Manages configuration files and reference data for Emm1typer"""
    
    def __init__(self, reference_dir):
        """
        Initialize configuration manager
        
        Args:
            reference_dir: Path to reference data directory
        """
        self.reference_dir = Path(reference_dir)
        
        # Reference files
        self.lineage_json = self.reference_dir / "lineage.json"
        self.probes_fa = self.reference_dir / "probes.fa"
        self.emm1_alleles = self.reference_dir / "emm1_alleles.txt"
        self.emm_types_yaml = self.reference_dir / "acceptable_emm_types.yaml"
        self.mlst_profiles_yaml = self.reference_dir / "acceptable_mlst_profiles.yaml"
        self.parse_script = Path(__file__).parent.parent / "scripts" / "parse_mykrobe_predict_emm1.py"
        
        # Load acceptable types from YAML files
        self.acceptable_emm_types = self._load_acceptable_emm_types()
        self.acceptable_mlst_profiles = self._load_acceptable_mlst_profiles()
        
        # Validate reference files
        self.validate_references()
    
    def _load_acceptable_emm_types(self):
        """Load acceptable emm types from YAML file"""
        try:
            with open(self.emm_types_yaml, 'r') as f:
                data = yaml.safe_load(f)
                return data['emm_types']
        except Exception as e:
            print(f"Error loading acceptable emm types from {self.emm_types_yaml}: {e}")
            # Fallback to hardcoded list
            return [f"emm1.{i}" for i in range(20)]
    
    def _load_acceptable_mlst_profiles(self):
        """Load acceptable MLST profiles from YAML file"""
        try:
            with open(self.mlst_profiles_yaml, 'r') as f:
                data = yaml.safe_load(f)
                return data['mlst_profiles']
        except Exception as e:
            print(f"Error loading acceptable MLST profiles from {self.mlst_profiles_yaml}: {e}")
            # Fallback to hardcoded list
            return ["ST28", "ST15", "ST101", "ST334", "ST403"]
    
    def validate_references(self):
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
    
    def get_reference_paths(self):
        """Get dictionary of all reference file paths"""
        return {
            'lineage_json': self.lineage_json,
            'probes_fa': self.probes_fa,
            'emm1_alleles': self.emm1_alleles,
            'parse_script': self.parse_script,
            'emm_types_yaml': self.emm_types_yaml,
            'mlst_profiles_yaml': self.mlst_profiles_yaml
        }
    
    def get_acceptable_types(self):
        """Get acceptable emm types and MLST profiles"""
        return {
            'emm_types': self.acceptable_emm_types,
            'mlst_profiles': self.acceptable_mlst_profiles
        }