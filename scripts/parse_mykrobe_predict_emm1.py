import json
import sys
import pandas as pd
from argparse import ArgumentParser

# Function to parse command-line arguments
def get_arguments():
    parser = ArgumentParser(description='Parse mykrobe predict JSON files')
    parser.add_argument('--jsons', required=True, nargs='+', help='JSON files output from mykrobe predict')
    parser.add_argument('--alleles', required=True, help='alleles.txt file that defines each genotype, its marker, and the human-readable name')
    parser.add_argument('--prefix', required=True, help='prefix for output files')
    return parser.parse_args()

# Function to extract information about genotype calls from the JSON data
def inspect_calls(full_lineage_data):
    genotype_details = full_lineage_data['calls_summary']
    genotype_list = list(genotype_details.keys())

    best_score = 0
    best_genotype = None

    for genotype in genotype_list:
        max_score = genotype_details[genotype]['tree_depth']
        actual_score = sum(list(genotype_details[genotype]['genotypes'].values()))
        
        if actual_score == max_score:
            best_score = actual_score
            best_genotype = genotype
        elif actual_score < max_score and actual_score > best_score:
            best_score = actual_score
            best_genotype = genotype

    best_calls = genotype_details[best_genotype]['genotypes']
    best_calls_vals = list(best_calls.values())
    poorly_supported_markers = []
    lowest_within_genotype_percents = {}
    final_markers = []

    for level in best_calls.keys():
        call_details = full_lineage_data['calls'][best_genotype].get(level)
        if call_details:
            call_details = call_details[list(call_details.keys())[0]]
            ref = call_details['info']['coverage']['reference']['median_depth']
            alt = call_details['info']['coverage']['alternate']['median_depth']
            try:
                percent_support = alt / (alt + ref)
            except ZeroDivisionError:
                percent_support = 0
            marker_string = f"{level} ({best_calls[level]}; {alt}/{ref})"
            final_markers.append(marker_string)
        else:
            lowest_within_genotype_percents[0] = level
            marker_string = f"{level} (0)"
            poorly_supported_markers.append(marker_string)
            final_markers.append(marker_string)

        if best_calls[level] < 1:
            lowest_within_genotype_percents[percent_support] = level
            poorly_supported_markers.append(marker_string)

    if best_calls_vals.count(0) == 0 and best_calls_vals.count(0.5) == 0:
        confidence = 'strong'
        lowest_support_val = ''
    elif best_calls_vals.count(0) == 0 and best_calls_vals.count(0.5) == 1:
        confidence = 'moderate' if min(lowest_within_genotype_percents.keys()) > 0.5 else 'weak'
        lowest_support_val = round(min(lowest_within_genotype_percents.keys()), 3)
    else:
        confidence = 'weak'
        lowest_support_val = round(min(lowest_within_genotype_percents.keys()), 3)

    non_matching_markers = []
    non_matching_supports = []
    if len(genotype_list) > 1:
        genotype_list.remove(best_genotype)
        for genotype in genotype_list:
            other_calls = genotype_details[genotype]['genotypes']
            for call in other_calls.keys():
                if call not in best_calls.keys():
                    call_info = full_lineage_data['calls'][genotype][call]
                    if call_info:
                        call_info = call_info[list(call_info.keys())[0]]
                        ref_depth = call_info['info']['coverage']['reference']['median_depth']
                        alt_depth = call_info['info']['coverage']['alternate']['median_depth']
                        if alt_depth >= 1:
                            percent_support = alt_depth / (alt_depth + ref_depth)
                            non_matching_supports.append(percent_support)
                            marker_string = f"{call} ({other_calls[call]}; {alt_depth}/{ref_depth})"
                            non_matching_markers.append(marker_string)

    max_non_matching = round(max(non_matching_supports), 3) if non_matching_supports else ''

    return best_genotype, confidence, lowest_support_val, poorly_supported_markers, max_non_matching, non_matching_markers, final_markers

# Function to extract lineage information and return as DataFrame
def extract_lineage_info(lineage_data, genome_name, lineage_name_dict):
    lineage_out_dict = {}

    # Ensure genome_name is always included
    lineage_out_dict['genome'] = [genome_name]

    # Access 'lineage' and 'calls_summary' to extract final genotype
    lineage_summary = lineage_data.get('lineage', {}).get('lineage')
    
    if len(lineage_summary) == 0:
        lineage_out_dict['final genotype'] = ['uncalled']
        lineage_out_dict['name']  = ['NA']
        lineage_out_dict['confidence'] = ['NA']
        lineage_out_dict['lowest support for genotype marker']  = ['']
        lineage_out_dict['poorly supported markers']  = ['']
        lineage_out_dict['max support for additional markers']  = ['']
        lineage_out_dict['additional markers']  = ['']
        lineage_out_dict['node support'] = ['']
    else:
        best_genotype, confidence, lowest_support_val, poorly_supported_markers, non_matching_support, non_matching_markers, final_markers = inspect_calls(lineage_data['lineage'])

        # Correct name assignment: 3rd column in alleles.txt is the genotype, 4th column is the name
        lineage_name = lineage_name_dict.get(best_genotype, best_genotype)  # Use name if available, else use the genotype itself
        lineage_out_dict['final genotype'] = [best_genotype]
        lineage_out_dict['name'] = [lineage_name]
        lineage_out_dict['confidence'] = [confidence]
        lineage_out_dict['lowest support for genotype marker'] = [lowest_support_val]
        lineage_out_dict['poorly supported markers'] = ['; '.join(poorly_supported_markers)]
        lineage_out_dict['max support for additional markers'] = [non_matching_support]
        lineage_out_dict['additional markers'] = ['; '.join(non_matching_markers)]
        lineage_out_dict['node support'] = ['; '.join(final_markers)]
    
    return pd.DataFrame(lineage_out_dict)

# Main function to process the files
def main():
    args = get_arguments()
    results_tables = []
    lineage_name_dict = {}

    # Read alleles mapping file
    with open(args.alleles, 'r') as lineage_names:
        for line in lineage_names:
            fields = line.strip().split('\t')
            # The 3rd column has the genotype and 4th column has the human-readable name
            lineage_name_dict[fields[2]] = fields[3]

    for json_file in args.jsons:
        with open(json_file) as f:
            myk_result = json.load(f)
        
        if len(list(myk_result.keys())) > 1:
            print(f"More than one result in mykrobe output file {json_file}, quitting")
            sys.exit()
        
        genome_name = list(myk_result.keys())[0]
        genome_data = myk_result[genome_name]
        lineage_data = genome_data["phylogenetics"]
        lineage_table = extract_lineage_info(lineage_data, genome_name, lineage_name_dict)
        results_tables.append(lineage_table)

    final_results = pd.concat(results_tables, sort=True)
    
    # Write to CSV with the correct columns (no species column)
    final_results.to_csv(f"{args.prefix}_predictResults.tsv", index=False, sep="\t", 
                         columns=["genome", "final genotype", "name", 
                                  "confidence", "lowest support for genotype marker", 
                                  "poorly supported markers", "max support for additional markers", 
                                  "additional markers", "node support"])

if __name__ == '__main__':
    main()

