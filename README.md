# Emm1typer

A tool for genotyping and lineage determination of Streptococcus pyogenes emm1 isolates.

## Overview

Emm1typer provides two main functions:

1. **Standard Mode**: emm1 lineage typing from paired-end reads using mykrobe
2. **QC Mode**: Quality control assessment of assembled contigs

## Installation

### Using pip (recommended)

```bash
pip install emm1typer
```

### From source

```bash
git clone https://github.com/JA-Lacey/Emm1Typer.git
cd Emm1Typer
pip install -e .
```

## Requirements

### External Tools (must be installed separately)

- `mykrobe` (tested with version 0.12.1) - for lineage typing
- `mlst` - for MLST analysis
- `emmtyper` - for emm typing
- `seqkit` - for assembly statistics

### Python Dependencies (installed automatically)

- `pandas>=1.3.0`
- `pyyaml>=5.4.0`


### Reference Files
Required files in the `reference_data/` directory:
- `lineage.json` - lineage definitions
- `probes.fa` - probe sequences
- `emm1_alleles.txt` - allele mapping
- `acceptable_emm_types.yaml` - acceptable EMM types
- `acceptable_mlst_profiles.yaml` - acceptable MLST profiles
- `acceptable_assembly_metrics.json` - assembly quality thresholds

## Usage

### Standard Mode (Lineage Typing)
```bash
emm1typer --reads reads.tab --reference-dir ./reference_data
```

### QC Mode (Quality Control)
```bash
emm1typer --qc --contigs contigs.tab --reference-dir ./reference_data
```

### Combined Mode
```bash
emm1typer --reads reads.tab --contigs contigs.tab --reference-dir ./reference_data
```

## Input Files

### Reads file (reads.tab)
Tab-separated file with strain ID and paired read paths:
```
Sample001	/path/to/sample001_R1.fastq.gz	/path/to/sample001_R2.fastq.gz
Sample002	/path/to/sample002_R1.fastq.gz	/path/to/sample002_R2.fastq.gz
```

### Contigs file (contigs.tab)
Tab-separated file with strain ID and contig paths:
```
Sample001	/path/to/sample001_contigs.fa
Sample002	/path/to/sample002_contigs.fa
```

## Outputs

### Standard Mode

- `mykrobe_predictResults.tsv` - lineage typing results with final genotypes

### QC Mode  

- `qc_summary.tsv` - quality control results with EMM types, MLST, lineages, and pass/fail status

## Options

- `--threads` - Number of threads (default: 8)
- `--output-dir` - Output directory (default: emm1typer_output)

## Quality Control Checks

QC mode validates:
- EMM type (accepts EMM1.* variants)
- MLST sequence type 
- Assembly quality (genome size, contig count, N50)

Results are marked as PASS or FAIL with explanatory comments.