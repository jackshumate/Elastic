import json
import csv

# Load the data files
with open('ilm_explain.json', 'r') as ilm_file:
    ilm_data = json.load(ilm_file)

with open('cat_shards.txt', 'r') as shards_file:
    shards_data = shards_file.readlines()

with open('cat_nodes.txt', 'r') as nodes_file:
    nodes_data = nodes_file.readlines()

# Parse the node roles
node_roles = {}
for line in nodes_data[1:]:
    parts = line.split()
    node_id = parts[0]
    roles = parts[2]
    node_roles[node_id] = roles

# Prepare for output
output_data = []

# Process ILM data
for index, index_data in ilm_data.items():
    ilm_phase = index_data.get('lifecycle', {}).get('phase', 'unknown')  # Handle missing 'lifecycle' key gracefully
    for shard in shards_data:
        if index in shard:
            shard_parts = shard.split()
            shard_id = shard_parts[0]
            node_id = shard_parts[1]
            node_role = node_roles.get(node_id, "")
            
            # Determine the correct node tier based on the ILM phase
            if ilm_phase == "hot" and "h" in node_role:
                node_tier = "hot"
            elif ilm_phase == "warm" and "w" in node_role:
                node_tier = "warm"
            elif ilm_phase == "cold" and "c" in node_role:
                node_tier = "cold"
            elif ilm_phase == "frozen" and "f" in node_role:
                node_tier = "frozen"
            else:
                node_tier = f"{node_role}*"
            
            output_data.append([index, ilm_phase, shard_id, node_id, node_tier])

# Write to CSV
with open('ilm_shard_mismatches.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Index Name", "ILM Phase", "Shard ID", "Shard Location", "Node Tier"])
    writer.writerows(output_data)

print("Audit completed! Results saved in ilm_shard_mismatches.csv")
