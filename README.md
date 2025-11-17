# Emm1typer

A comprehensive tool for emm1 lineage typing, MLST analysis, and emmtyping of Streptococcus pyogenes isolates.

## 🆕 Modular Design

This tool has been refactored into a **modular architecture** for easier maintenance and modification. You can now use either:

- **`Emm1typer_modular.py`** - New modular version (recommended)
- **`Emm1typer.py`** - Original monolithic version

### Modular Architecture Benefits

- **Easier maintenance**: Each function is in its own focused module
- **Simple modifications**: Change specific functionality without affecting other components
- **Better testing**: Test individual modules independently
- **Cleaner code**: Separation of concerns and single responsibility principle
- **Extensible**: Easy to add new analysis types or modify existing ones

### Module Structure

```
modules/
├── __init__.py                 # Package initialization
├── config_manager.py           # Configuration and reference file management
├── dependency_checker.py       # External tool validation
├── lineage_typer.py            # emm1 lineage typing using mykrobe
├── mlst_analyzer.py            # MLST analysis using mlst
├── emm_typer.py                # emm typing using emmtyper
├── results_analyzer.py         # Results filtering and validation
└── report_generator.py         # Summary report generation
```

## Features

- **emm1 lineage typing** from paired-end reads using mykrobe
- **MLST typing** from assembled contigs using mlst
- **emmtyping** from assembled contigs using emmtyper
- Parallel processing support for high-throughput analysis
- **Configurable acceptable types** via YAML files for easy modification
- **Automated warnings** for samples with non-acceptable emm types and MLST profiles
- Comprehensive summary reporting
- **🆕 Modular design** for easy customization and maintenance

## Requirements

### External Tools
- `mykrobe` - for emm1 lineage typing
- `mlst` - for MLST analysis (with spyogenes scheme)
- `emmtyper` - for emm typing
- `parallel` (GNU parallel) - for parallel processing
- `python3` with pandas and PyYAML

### Reference Data
The script requires the following reference files in the `reference_data/` directory:
- `lineage.json` - mykrobe lineage configuration
- `probes.fa` - probe sequences for mykrobe
- `emm1_alleles.txt` - allele definitions
- `acceptable_emm_types.yaml` - configurable list of acceptable emm types
- `acceptable_mlst_profiles.yaml` - configurable list of acceptable MLST profiles
- `parse_mykrobe_predict_emm1.py` - parsing script (in scripts/ directory)

## Configuration

### Acceptable emm Types (reference_data/acceptable_emm_types.yaml)
Edit this file to modify which emm types are considered acceptable:
```yaml
# Acceptable emm types for S. pyogenes emm1 analysis
emm_types:
  - "emm1.0"
  - "emm1.1"
  - "emm1.2"
  # ... add more types as needed
```

### Acceptable MLST Profiles (reference_data/acceptable_mlst_profiles.yaml)
Edit this file to modify which MLST sequence types are considered acceptable:
```yaml
# Acceptable MLST profiles for S. pyogenes emm1 analysis
mlst_profiles:
  - "ST28"
  - "ST15"
  - "ST101"
  # ... add more STs as needed
```

## Usage

### Modular Version (Recommended)

```bash
# Process reads only (emm1 lineage typing)
python Emm1typer_modular.py --reads reads.tab --reference-dir ./reference_data

# Process contigs only (MLST + emmtyping)
python Emm1typer_modular.py --contigs contigs.tab --reference-dir ./reference_data

# Process both reads and contigs (complete analysis)
python Emm1typer_modular.py --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data
```

### Original Version

```bash
# Process reads only (emm1 lineage typing)
python Emm1typer.py --reads reads.tab --reference-dir ./reference_data

# Process contigs only (MLST + emmtyping)
python Emm1typer.py --contigs contigs.tab --reference-dir ./reference_data

# Process both reads and contigs (complete analysis)
python Emm1typer.py --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data
```

### Advanced Options

```bash
python Emm1typer_modular.py \
  --reads reads.tab \
  --contigs contigs.tab \
  --reference-dir ./reference_data \
  --output-dir my_analysis_results \
  --threads 16 \
  --parallel-jobs 20
```

## Modifying the Workflow

### Adding New Analysis Types

To add a new analysis type to the modular version:

1. **Create a new module** in `modules/` (e.g., `new_analyzer.py`):
   ```python
   class NewAnalyzer:
       def __init__(self, output_dir, threads=8):
           self.output_dir = Path(output_dir)
           self.threads = threads
       
       def process_data(self, input_file):
           # Your analysis logic here
           return True
   ```

2. **Import and initialize** in `Emm1typer_modular.py`:
   ```python
   from modules.new_analyzer import NewAnalyzer
   
   # In __init__:
   self.new_analyzer = NewAnalyzer(output_dir, threads)
   ```

3. **Add to the workflow** in the orchestrator class:
   ```python
   def run_new_analysis(self, input_file):
       return self.new_analyzer.process_data(input_file)
   ```

### Modifying Existing Analysis

To modify an existing analysis (e.g., MLST):

1. **Edit the specific module**: `modules/mlst_analyzer.py`
2. **Modify only the relevant methods** without affecting other components
3. **The changes automatically apply** to the main workflow

### Customizing Results Analysis

To change how results are filtered or analyzed:

1. **Edit** `modules/results_analyzer.py`
2. **Modify** the `analyze_mlst_results()` or `analyze_emmtyper_results()` methods
3. **Add new filtering criteria** or change existing logic

## Input File Formats

### Reads File (reads.tab)
Tab-separated file with three columns (no header):
```
Strain_ID	reads1_path	reads2_path
Sample001	/path/to/sample001_R1.fastq.gz	/path/to/sample001_R2.fastq.gz
Sample002	/path/to/sample002_R1.fastq.gz	/path/to/sample002_R2.fastq.gz
```

### Contigs File (contigs.tab)
Tab-separated file with two columns (no header):
```
Strain_ID	contigs_path
Sample001	/path/to/sample001_contigs.fa
Sample002	/path/to/sample002_contigs.fa
```

## Output and Warnings

The script provides clear visual feedback during analysis:

### Warning Messages
The script will display warnings for samples that don't meet acceptance criteria:
```
⚠️  WARNING: Samples with non-acceptable MLST profiles:
   - Sample001: ST1 (not in acceptable list)
   - Sample002: ST5 (not in acceptable list)
   Acceptable MLST profiles: ST28, ST15, ST101, ST334, ST403, ...

⚠️  WARNING: Samples with non-acceptable emm types:
   - Sample003: emm12.0 (not in acceptable list)
   Acceptable emm types: emm1.0, emm1.1, emm1.2, ...
```

### Success Messages
```
✓ Found 5 samples with acceptable MLST profiles
✓ Found 3 samples with acceptable emm types
```

## Output Files

The script generates several output files:

### emm1 Lineage Results (from reads)
- `emm1_lineage_results_predictResults.tsv` - Complete lineage typing results
- Includes confidence scores and marker support information

### MLST Results (from contigs)
- `mlst_results.tsv` - Complete MLST results
- `mlst_results.json` - MLST results in JSON format
- `acceptable_mlst_results.tsv` - Filtered results for acceptable ST types

### emmtyper Results (from contigs)
- `emmtyper_results.tsv` - Complete emmtyper results
- `acceptable_emmtyper_results.tsv` - Filtered results for acceptable emm types

### Summary
- `Emm1typer_summary_report.txt` - Comprehensive analysis summary

## Command Line Options

- `--reads` - Tab-separated file with strain IDs and paired read paths
- `--contigs` - Tab-separated file with strain IDs and contig paths
- `--reference-dir` - Directory containing reference data (required)
- `--output-dir` - Output directory for results (default: emm1typer_output)
- `--threads` - Number of threads for analysis tools (default: 8)
- `--parallel-jobs` - Number of parallel jobs for mykrobe (default: 10)
- `--skip-deps-check` - Skip dependency checking

## Example Workflow

1. **Configure acceptable types** by editing the YAML files in `reference_data/`:
   - `acceptable_emm_types.yaml`
   - `acceptable_mlst_profiles.yaml`

2. **Prepare your input files** following the format specifications

3. **Run the analysis** (modular version recommended):
   ```bash
   python Emm1typer_modular.py --reads my_reads.tab --contigs my_contigs.tab --reference-dir ./reference_data
   ```

4. **Review the output** for warnings about non-acceptable samples

5. **Check results**:
   - Summary report: `emm1typer_output/Emm1typer_summary_report.txt`
   - Filtered results: `acceptable_*_results.tsv` files
   - Complete results: `*_results.tsv` files

## Notes

- **🆕 Modular design**: Use `Emm1typer_modular.py` for easier customization and maintenance
- **Configurable acceptance criteria**: Simply edit the YAML files to change which emm types and MLST profiles are considered acceptable
- **Clear warnings**: The script provides immediate feedback about samples that don't meet your criteria
- **Automatic filtering**: Results are automatically separated into complete and filtered (acceptable-only) datasets
- **Fallback protection**: If YAML files can't be read, the script falls back to sensible defaults
- The script performs emm1 lineage typing as described in your workflow using mykrobe with custom lineage and probe sets
- MLST analysis uses the spyogenes scheme specifically
- The script includes comprehensive error checking and dependency validation

## Troubleshooting

If you encounter issues:
1. Ensure all required tools are installed and in your PATH
2. Verify that reference files are present and correctly formatted
3. Check that input file paths are correct and accessible
4. Make sure PyYAML is installed: `pip install PyYAML`
