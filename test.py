import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# --- Load CSVs ---
nodes_df = pd.read_csv("coretweet_nodes_with_communities.csv")  # columns: Id, Community
edges_df = pd.read_csv("coretweet_edges.csv")                   # columns: source, target, weight

# --- Build Graph ---
G = nx.Graph()

# Add nodes (with community attribute)
for _, row in nodes_df.iterrows():
    G.add_node(str(row["Id"]), community=row["Community"])

# Add edges (with weight if present)
if "weight" in edges_df.columns:
    for _, row in edges_df.iterrows():
        G.add_edge(str(row["source"]), str(row["target"]), weight=row["weight"])
else:
    for _, row in edges_df.iterrows():
        G.add_edge(str(row["source"]), str(row["target"]))

print(f"Graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# --- Prepare colors ---
communities = [G.nodes[n]["community"] for n in G.nodes()]
unique_comms = sorted(set(communities))
color_map = cm.get_cmap("tab20", len(unique_comms))
color_idx = [unique_comms.index(c) for c in communities]
node_colors = [color_map(i) for i in color_idx]

# --- ForceAtlas2 layout ---
pos = nx.forceatlas2_layout(G, max_iter=1000, scaling_ratio=100)

# --- Plot ---
plt.figure(figsize=(14, 12))
nx.draw_networkx_edges(G, pos, alpha=0.2, width=0.4)
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=40, edgecolors="black", linewidths=0.3)
plt.title(f"Co-Retweet Network ({len(unique_comms)} communities)", fontsize=14)
plt.axis("off")
plt.tight_layout()
plt.show()
