import json
import csv

# 1. Load ILM Explain Data (from ilm_explain.json)
def get_ilm_explain_from_file():
    with open("ilm_explain.json") as ilm_file:
        ilm_data = json.load(ilm_file)
    return ilm_data

# 2. Load Shard Allocation Data (from cat_shards.txt)
def get_cat_shards_from_file():
    with open("cat_shards.txt") as shard_file:
        shard_data = shard_file.readlines()
    return shard_data

# 3. Load Node Information (from cat_nodes.txt)
def get_cat_nodes_from_file():
    with open("cat_nodes.txt") as nodes_file:
        nodes_data = nodes_file.readlines()
    return nodes_data

# 4. Parse Node Roles from cat_nodes.txt
def parse_node_roles(node_data):
    node_roles = {}
    for line in node_data[1:]:  # Skip the header
        parts = line.split()
        node_name = parts[0]
        roles = parts[1:]
        node_roles[node_name] = roles
    return node_roles

# 5. Compare ILM Phase with Shard Allocation
def compare_ilm_and_shards(ilm_data, shard_data, node_roles):
    mismatches = []
    ilm_indices = {}

    # Extract the ILM phase for each index
    for index, details in ilm_data['indices'].items():
        ilm_phase = details['lifecycle']['phase']
        ilm_indices[index] = ilm_phase

    # Parse shard data and compare with ILM phase
    for line in shard_data[1:]:  # Skip the header
        parts = line.split()
        index_name = parts[0]
        shard_id = parts[1]
        node_name = parts[-1]

        # Get the ILM phase for this index
        ilm_phase = ilm_indices.get(index_name)

        # Get the node roles for the current node
        node_role = node_roles.get(node_name, [])

        # Determine the "node tier" based on node role
        if "c" in node_role:
            node_tier = "cold"
        elif "w" in node_role:
            node_tier = "warm"
        elif "h" in node_role:
            node_tier = "hot"
        elif "f" in node_role:
            node_tier = "frozen"
        else:
            node_tier = "unknown"  # In case we encounter a node with no recognized role

        # Check for mismatches (ILM phase doesn't match the node tier)
        if ilm_phase == "cold" and node_tier != "cold":
            mismatches.append((index_name, ilm_phase, shard_id, node_name, node_tier + "*"))
        elif ilm_phase == "warm" and node_tier != "warm":
            mismatches.append((index_name, ilm_phase, shard_id, node_name, node_tier + "*"))
        elif ilm_phase == "hot" and node_tier != "hot":
            mismatches.append((index_name, ilm_phase, shard_id, node_name, node_tier + "*"))
        elif ilm_phase == "frozen" and node_tier != "frozen":
            mismatches.append((index_name, ilm_phase, shard_id, node_name, node_tier + "*"))
        else:
            # No mismatch, simply add the node tier without a "*" (it's correctly allocated)
            mismatches.append((index_name, ilm_phase, shard_id, node_name, node_tier))

    return mismatches

# 6. Export results to CSV
def export_results_to_csv(mismatches, output_file='ilm_shard_mismatches.csv'):
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Index Name', 'ILM Phase', 'Shard ID', 'Shard Location', 'Node Tier'])

        for mismatch in mismatches:
            writer.writerow(mismatch)

    print(f"Results exported to {output_file}")

# 7. Main function to run the script
def main():
    # Load all data from files
    ilm_data = get_ilm_explain_from_file()
    shard_data = get_cat_shards_from_file()
    node_data = get_cat_nodes_from_file()

    # Parse node roles
    node_roles = parse_node_roles(node_data)

    # Compare ILM phase with shard allocation
    mismatches = compare_ilm_and_shards(ilm_data, shard_data, node_roles)

    # Output mismatches if found
    if mismatches:
        print("Mismatches found:")
        for mismatch in mismatches:
            print(f"Index: {mismatch[0]}, ILM Phase: {mismatch[1]}, Shard: {mismatch[2]}, Shard Location: {mismatch[3]}, Node Tier: {mismatch[4]}")
        
        # Export to CSV
        export_results_to_csv(mismatches)
    else:
        print("No mismatches found.")

# Run the script
if __name__ == "__main__":
    main()
