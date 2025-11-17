#!/usr/bin/env python3
"""
Dependency Checker for Emm1typer

Validates that all required external tools are available.
"""

import sys
import subprocess


class DependencyChecker:
    """Checks for required external tools and dependencies"""
    
    def __init__(self):
        """Initialize dependency checker"""
        self.required_tools = ['mykrobe', 'mlst', 'emmtyper', 'parallel']
    
    def check_dependencies(self):
        """Check if required external tools are available"""
        missing_tools = []
        
        for tool in self.required_tools:
            if not self._is_tool_available(tool):
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"Error: Missing required tools: {', '.join(missing_tools)}")
            print("Please install the missing tools before running this script.")
            print("\nInstallation suggestions:")
            for tool in missing_tools:
                suggestion = self._get_install_suggestion(tool)
                print(f"  {tool}: {suggestion}")
            sys.exit(1)
        
        print("✓ All required tools are available")
    
    def _is_tool_available(self, tool):
        """Check if a specific tool is available in PATH"""
        try:
            subprocess.run([tool, '--help'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _get_install_suggestion(self, tool):
        """Get installation suggestion for a missing tool"""
        suggestions = {
            'mykrobe': 'conda install -c bioconda mykrobe or pip install mykrobe',
            'mlst': 'conda install -c bioconda mlst',
            'emmtyper': 'conda install -c bioconda emmtyper',
            'parallel': 'sudo apt-get install parallel (Ubuntu/Debian) or brew install parallel (macOS)'
        }
        return suggestions.get(tool, 'Please check tool documentation for installation instructions')
    
    def get_tool_versions(self):
        """Get versions of available tools for reporting"""
        versions = {}
        for tool in self.required_tools:
            if self._is_tool_available(tool):
                try:
                    result = subprocess.run([tool, '--version'], capture_output=True, text=True)
                    versions[tool] = result.stdout.strip().split('\n')[0]
                except:
                    versions[tool] = "version unknown"
            else:
                versions[tool] = "not available"
        return versions