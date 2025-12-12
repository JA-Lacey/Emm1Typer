# Emm1typer

A simplified tool for emm1 lineage typing of Streptococcus pyogenes isolates.

## Overview

Emm1typer provides two main modes of operation:

1. **Standard Mode**: Run mykrobe analysis for emm1 lineage typing from reads
2. **QC Mode**: Quality control assessment of assembled contigs including emmtyper, MLST, and assembly statistics

## Features

- **Standard Mode**: emm1 lineage typing from paired-end reads using mykrobe
- **QC Mode**: Comprehensive quality control including:
  - emmtyping using emmtyper
  - MLST analysis using mlst (spyogenes scheme)
  - Assembly quality assessment using seqkit stats
  - Validation against configurable acceptable values
- **Flexible EMM validation**: Accepts any EMM1.* variant including partial matches with `~`
- **Configurable thresholds**: Easy modification of acceptable values via YAML/JSON files
- Automated pass/fail quality control status with detailed comments

## Requirements

### External Tools
- `mykrobe` - for emm1 lineage typing (standard mode)
- `mlst` - for MLST analysis (QC mode)
- `emmtyper` - for emm typing (QC mode)
- `seqkit` - for assembly statistics (QC mode)
- `python3` with pandas and PyYAML

### Reference Data
The tool requires reference files in the `reference_data/` directory:
- `acceptable_emm_types.yaml` - configurable list of acceptable EMM types
- `acceptable_mlst_profiles.yaml` - configurable list of acceptable MLST profiles  
- `acceptable_assembly_metrics.json` - assembly quality thresholds
- Additional files for standard mykrobe mode (lineage.json, probes.fa, etc.)

## Configuration Files

### Acceptable EMM Types (`reference_data/acceptable_emm_types.yaml`)
The QC mode uses intelligent pattern matching for EMM1 variants:
```yaml
# Acceptable emm types for S. pyogenes emm1 analysis
# Includes all EMM1.* variants and allows for ~ partial matches
emm_types:
  - "emm1.0"
  - "emm1.1"
  - "emm1.34"
  - "emm1.34~"
  - "emm1.90"
  - "emm1.92"
  - "emm1.96"
  - "emm1.98"
  - "emm1.99"
  # Pattern matching enabled in QC processor for EMM1.* and EMM1.*~ variants
```

**Note**: The QC mode automatically accepts ANY EMM1.* variant (e.g., EMM1.123, emm1.999~) even if not explicitly listed.

### Acceptable MLST Profiles (`reference_data/acceptable_mlst_profiles.yaml`)
```yaml
# Acceptable MLST profiles for S. pyogenes emm1 analysis
mlst_profiles:
  - "28"
  - "440"
  - "542"
  - "643"
  - "785"
  - "830"
  - "852"
  # ... additional acceptable ST values
  - "-"  # Allows for failed/unknown MLST typing
```

### Assembly Quality Metrics (`reference_data/acceptable_assembly_metrics.json`)
```json
{
  "min_genome_size": 1800000,
  "max_genome_size": 2200000,
  "max_contigs": 100,
  "min_n50": 50000,
  "max_n_content": 5.0
}
```

## Usage

### QC Mode (Quality Control of Assembled Contigs)
```bash
# Basic QC analysis
python Emm1typer.py --qc --contigs contigs.tab --reference-dir ./reference_data

# QC analysis with custom output directory and threads
python Emm1typer.py --qc --contigs contigs.tab --reference-dir ./reference_data \
  --output-dir qc_results --threads 16
```

### Standard Mode (Mykrobe Analysis)
```bash
# Standard mykrobe analysis from reads
python Emm1typer.py --reads reads.tab --reference-dir ./reference_data

# With custom options
python Emm1typer.py --reads reads.tab --reference-dir ./reference_data \
  --output-dir mykrobe_results --threads 16
```

## Input File Formats

### Contigs File for QC Mode (contigs.tab)
Tab-separated file with two columns (no header):
```
Strain_ID	contigs_path
Sample001	/path/to/sample001_contigs.fa
Sample002	/path/to/sample002_contigs.fa
Sample003	/path/to/sample003_contigs.fasta
```

### Reads File for Standard Mode (reads.tab)
Tab-separated file with three columns (no header):
```
Strain_ID	reads1_path	reads2_path
Sample001	/path/to/sample001_R1.fastq.gz	/path/to/sample001_R2.fastq.gz
Sample002	/path/to/sample002_R1.fastq.gz	/path/to/sample002_R2.fastq.gz
```

## QC Mode Output

### Main Output File: `qc_summary.tsv`
Contains the following columns for each strain:
- **Strain_ID**: Sample identifier
- **ST**: MLST sequence type (from mlst tool)
- **EMM**: EMM type (from emmtyper tool)
- **Lineage**: Determined lineage based on EMM and ST
- **QC_Status**: PASS or FAIL based on all quality checks
- **Comments**: Detailed explanations of any issues or "All QC checks passed"

### Example QC Output:
```
Strain_ID	ST	EMM	Lineage	QC_Status	Comments
Sample001	28	EMM1.0	emm1.0	PASS	All QC checks passed
Sample002	440	EMM1.34~	emm1_variant	PASS	All QC checks passed
Sample003	999	EMM1.90	emm1_variant	FAIL	ST 999 not in acceptable list
Sample004	28	EMM2.0	non-emm1	FAIL	EMM type EMM2.0 not acceptable (must be EMM1.* variant)
```

## Quality Control Checks

The QC mode performs the following validations:

### 1. EMM Type Validation
- ✅ **Accepts**: Any EMM1.* variant (case-insensitive)
- ✅ **Handles**: Partial matches with `~` (e.g., EMM1.34~)
- ❌ **Rejects**: Non-EMM1 types (e.g., EMM2.0, EMM12.1)

### 2. MLST Validation
- ✅ **Accepts**: ST values listed in `acceptable_mlst_profiles.yaml`
- ✅ **Handles**: Unknown/failed typing (`-`)
- ❌ **Rejects**: ST values not in the acceptable list

### 3. Assembly Quality Validation
- **Genome size**: Must be between 1.8-2.2 Mb
- **Contig count**: Must be ≤100 contigs
- **N50**: Must be ≥50,000 bp
- **N content**: Must be ≤5%

## Command Line Options

- `--qc` - Enable QC mode for contig analysis
- `--reads` - Tab-separated file with strain IDs and paired read paths (standard mode)
- `--contigs` - Tab-separated file with strain IDs and contig paths (QC mode)
- `--reference-dir` - Directory containing reference data (required)
- `--output-dir` - Output directory for results (default: emm1typer_output)
- `--threads` - Number of threads for analysis tools (default: 8)

## Project Structure

```
Emm1typer/
├── Emm1typer.py              # Main entry point
├── scripts/
│   ├── __init__.py
│   ├── qc_processor.py       # QC mode implementation
│   └── parse_mykrobe_predict_emm1.py
├── reference_data/
│   ├── acceptable_emm_types.yaml
│   ├── acceptable_mlst_profiles.yaml
│   ├── acceptable_assembly_metrics.json
│   └── [other reference files]
├── example_contigs.tab       # Example input file
├── example_reads.tab         # Example input file
└── README.md
```

## Examples

### Basic QC Analysis
```bash
python Emm1typer.py --qc --contigs my_contigs.tab --reference-dir ./reference_data
```

### QC Analysis with Custom Settings
```bash
python Emm1typer.py --qc \
  --contigs my_contigs.tab \
  --reference-dir ./reference_data \
  --output-dir qc_analysis_results \
  --threads 12
```

### Standard Mykrobe Analysis
```bash
python Emm1typer.py --reads my_reads.tab --reference-dir ./reference_data
```

## Troubleshooting

### Common Issues:
1. **Tool not found errors**: Ensure emmtyper, mlst, seqkit, and mykrobe are installed and in PATH
2. **Reference file errors**: Verify all YAML/JSON files exist and are properly formatted
3. **Input file errors**: Check that contig/read file paths are correct and accessible
4. **Python module errors**: Install required packages: `pip install pandas PyYAML`

### Dependency Installation:
```bash
# Install required Python packages
pip install pandas PyYAML

# Install external tools (example for conda)
conda install -c bioconda emmtyper mlst seqkit mykrobe= pandas PyYAML 
```

## Notes

- The tool automatically handles case-insensitive EMM type matching
- Assembly quality thresholds can be customized by editing the JSON configuration file
- QC mode is designed for rapid quality assessment of large batches of assembled genomes
- The `~` character in EMM types indicates partial/uncertain matches from emmtyper and is handled appropriatelyq