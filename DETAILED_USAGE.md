# Emm1typer - Detailed Usage Guide

## Table of Contents
- [Installation and Setup](#installation-and-setup)
- [Detailed Command Options](#detailed-command-options)
- [Input File Formats](#input-file-formats)
- [Reference Data Configuration](#reference-data-configuration)
- [Output File Descriptions](#output-file-descriptions)
- [Quality Control Details](#quality-control-details)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Advanced Configuration](#advanced-configuration)

## Installation and Setup

### Dependencies
Emm1typer requires the following external tools to be installed and available in your PATH:

- **mykrobe** (tested with version 0.12.1)
- **mlst** - for MLST analysis
- **emmtyper** - for emm typing
- **seqkit** - for assembly statistics

### Python Requirements
```bash
pip install pandas pyyaml
```

### Reference Data Setup
Place all reference files in a single directory (typically `reference_data/`):

1. `lineage.json` - Lineage definitions for mykrobe
2. `probes.fa` - Probe sequences for mykrobe
3. `emm1_alleles.txt` - Mapping of genotypes to human-readable names
4. `acceptable_emm_types.yaml` - List of acceptable EMM types
5. `acceptable_mlst_profiles.yaml` - List of acceptable MLST profiles
6. `acceptable_assembly_metrics.json` - Assembly quality thresholds

## Detailed Command Options

### Standard Mode (Lineage Typing)
```bash
python Emm1typer.py --reads <reads_file> --reference-dir <ref_dir> [options]
```

**Required:**
- `--reads` - Tab-separated file with strain IDs and read paths
- `--reference-dir` - Directory containing reference data

**Optional:**
- `--output-dir` - Output directory (default: emm1typer_output)
- `--threads` - Number of parallel threads (default: 8)

### QC Mode (Quality Control)
```bash
python Emm1typer.py --qc --contigs <contigs_file> --reference-dir <ref_dir> [options]
```

**Required:**
- `--qc` - Enable QC mode
- `--contigs` - Tab-separated file with strain IDs and contig paths
- `--reference-dir` - Directory containing reference data

### Combined Mode
```bash
python Emm1typer.py --reads <reads_file> --contigs <contigs_file> --reference-dir <ref_dir> [options]
```

## Input File Formats

### Reads File Format
Tab-separated file with three columns (no header):
```
Strain_ID	Read1_Path	Read2_Path
SAMN12345678	/data/reads/sample1_R1.fastq.gz	/data/reads/sample1_R2.fastq.gz
SAMN87654321	/data/reads/sample2_R1.fastq.gz	/data/reads/sample2_R2.fastq.gz
```

### Contigs File Format
Tab-separated file with two columns (no header):
```
Strain_ID	Contigs_Path
SAMN12345678	/data/assemblies/sample1_contigs.fa
SAMN87654321	/data/assemblies/sample2_contigs.fa
```

## Reference Data Configuration

### acceptable_emm_types.yaml
Lists acceptable EMM types. The tool also accepts any EMM1.* variant through pattern matching:
```yaml
emm_types:
  - emm1.0
  - EMM1.0
  - emm1.1
  - emm1.2
```

### acceptable_mlst_profiles.yaml
Lists acceptable MLST sequence types:
```yaml
mlst_profiles:
  - ST28
  - ST15
  - ST393
```

### acceptable_assembly_metrics.json
Assembly quality thresholds:
```json
{
  "min_genome_size": 1700000,
  "max_genome_size": 2200000,
  "max_contigs": 200,
  "min_n50": 50000,
  "max_n_content": 5.0
}
```

### emm1_alleles.txt
Maps genotype codes to human-readable names:
```
column1	column2	genotype_code	human_readable_name
...	...	lineage_B.3.4.1.1.1.1.1.1	Lineage B.3.4.1.1.1.1.1.1
```

## Output File Descriptions

### Standard Mode Output: mykrobe_predictResults.tsv
Contains lineage typing results with the following columns:
- `genome` - Strain identifier
- `final genotype` - Mykrobe-determined lineage (e.g., lineage_B.3.4.1.1.1.1.1.1)
- `name` - Human-readable lineage name
- `confidence` - Analysis confidence level
- `lowest support for genotype marker` - Lowest confidence marker
- `poorly supported markers` - List of markers with low support
- `max support for additional markers` - Highest confidence for non-lineage markers
- `additional markers` - Non-lineage markers detected
- `node support` - Support values for lineage tree nodes

### QC Mode Output: qc_summary.tsv
Contains quality control results with the following columns:
- `Strain_ID` - Strain identifier
- `ST` - MLST sequence type
- `EMM` - EMM type and cluster (e.g., "EMM1.0 A-C3")
- `Lineage` - Final genotype from mykrobe analysis
- `QC_Status` - PASS or FAIL
- `Comments` - Detailed QC check results

## Quality Control Details

### EMM Type Validation
- Accepts exact matches from acceptable_emm_types.yaml
- Pattern matching for EMM1.* variants (case-insensitive)
- Accepts variants with ~ suffix (e.g., EMM1.0~)

### MLST Validation
- Checks against acceptable_mlst_profiles.yaml
- Reports specific ST that failed validation

### Assembly Quality Checks
- **Genome Size**: 1.7 MB - 2.2 MB
- **Contig Count**: ≤ 200 contigs
- **N50**: ≥ 50,000 bp
- **N Content**: ≤ 5%

### Lineage Determination
- Uses actual mykrobe predict results when available
- Reuses existing results to avoid duplicate analysis
- Falls back to fresh mykrobe analysis if needed

## Performance Optimization

### Parallel Processing
Emm1typer uses parallel processing for improved performance:

- **Standard Mode**: Multiple mykrobe predict jobs run simultaneously
- **QC Mode**: Parallel analysis of multiple strains
- **Combined Mode**: Both modes benefit from parallelization

### Threading Recommendations
- **Small datasets (≤5 strains)**: 4-8 threads
- **Medium datasets (6-20 strains)**: 8-16 threads
- **Large datasets (>20 strains)**: 16-32 threads (or number of available cores)

### Performance Tips
- Use SSD storage for faster I/O
- Ensure sufficient RAM (≥8GB recommended for large datasets)
- Consider using more threads for mykrobe-heavy workloads

## Troubleshooting

### Common Issues

**Mykrobe fails with KeyError: 'ncbi_names_json'**
- This indicates an incompatible mykrobe version
- Fix: Modify mykrobe source code as described in installation notes
- Or downgrade to mykrobe v0.12.1

**EMM type validation fails**
- Check that emmtyper is properly installed
- Verify contig file paths are correct
- Ensure contigs are in proper FASTA format

**MLST analysis fails**
- Verify mlst tool is installed with spyogenes scheme
- Check that contig files exist and are readable

**Assembly statistics missing**
- Ensure seqkit is properly installed
- Verify contig files are valid FASTA format

### Debug Mode
Add verbose output by modifying the script to show detailed command outputs.

## Advanced Configuration

### Custom Reference Data
Users can modify reference files to:
- Add new acceptable EMM types or MLST profiles
- Adjust assembly quality thresholds
- Update lineage definitions

### Integration with Pipelines
Emm1typer can be integrated into bioinformatics pipelines:
- Input files can be generated programmatically
- Output files are in standard TSV format for downstream analysis
- Exit codes indicate success (0) or failure (non-zero)

### Batch Processing
For large datasets:
1. Split input files into smaller batches
2. Run multiple instances in parallel
3. Combine results using standard Unix tools