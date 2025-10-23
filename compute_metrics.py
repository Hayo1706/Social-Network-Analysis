import igraph as ig
import pandas as pd
import numpy as np
from collections import Counter
import matplotlib.pyplot as plt

# Load csv's

nodes_df = pd.read_csv("coretweet_nodes_with_communities.csv")   # columns: Id, Community
edges_df = pd.read_csv("coretweet_edges.csv")   # columns: source, target, weight


# --- Build graph ---
g = ig.Graph.DataFrame(
    edges_df,
    directed=False,
    vertices=nodes_df.rename(columns={"Id": "name"}),  # igraph expects 'name' for vertex id
    use_vids=False
)

# --- Attach community info ---
g.vs["community"] = nodes_df["Community"]

print("=== BASIC NETWORK STRUCTURE ===")
print(f"Number of vertices (nodes): {g.vcount()}")
print(f"Number of edges: {g.ecount()}")
print(f"Network density: {g.density():.4f}")

# Diameter and average path length (might be slow on very large networks)
if g.is_connected():
    print(f"Network diameter: {g.diameter()}")
    print(f"Average path length: {g.average_path_length():.2f}")
else:
    giant = g.clusters().giant()
    print(f"Network not connected; giant component size: {giant.vcount()}")
    print(f"Diameter (giant component): {giant.diameter()}")
    print(f"Average path length (giant component): {giant.average_path_length():.2f}")



# Get degrees
degrees = np.array(g.degree())
counts, bins = np.histogram(degrees, bins=15)
print("\n=== DEGREE DISTRIBUTION ===")
for i in range(len(counts)):
    print(f"Degree range {bins[i]} - {bins[i+1]}: {counts[i]} nodes")
# Plot histogram
plt.figure(figsize=(10,6))
bars = plt.bar(
    bins[:-1],
    counts,
    width=np.diff(bins),
    color='skyblue',
    edgecolor='black',
    align='edge',
    alpha=0.9
)

# Optional: subtle gradient for aesthetics
for bar in bars:
    bar.set_facecolor(plt.cm.Blues(bar.get_height()/max(counts)))
plt.title('Degree Distribution of Co-Retweet Network', fontsize=18)
plt.xlabel('Degree', fontsize=16)
plt.ylabel('Number of Nodes', fontsize=16)
# Grid for readability
plt.grid(axis='y', linestyle='--', alpha=0.7)
# Improve tick label readability
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)

plt.tight_layout()






print("\n=== CENTRALITY MEASURES ===")
deg_cent = g.degree()
close_cent = g.closeness()
bet_cent = g.betweenness()
eig_cent = g.eigenvector_centrality()
pagerank = g.pagerank()


def top_n(metric, n=5, label="metric"):
    top = np.argsort(metric)[-n:][::-1]
    for i in top:
        print(f"  {g.vs[i]['name']} — {label}: {metric[i]:.4f}")

print("Top 5 Degree Centrality:")
top_n(deg_cent, label="degree")
print("Top 5 Closeness Centrality:")
top_n(close_cent, label="closeness")
print("Top 5 Betweenness Centrality:")
top_n(bet_cent, label="betweenness")
print("Top 5 Eigenvector Centrality:")
top_n(eig_cent, label="eigenvector")


print("\n=== COMMUNITY STRUCTURE ===")
comms = g.vs["community"]
num_comms = len(set(comms))
print(f"Number of communities: {num_comms}")

# Count nodes per community
comm_counts = Counter(comms)
print("Top 10 largest communities:")
for c, count in comm_counts.most_common(10):
    print(f"  Community {c}: {count} nodes")

# Internal vs external edges per community
print("\nInternal vs External Edges per Community, sorted by size:")
for c, _ in comm_counts.most_common(10):
    nodes_in_comm = [v.index for v in g.vs if v["community"] == c]
    sub = g.subgraph(nodes_in_comm)
    internal = sub.ecount()
    total = sum(1 for e in g.es if (g.vs[e.source]["community"] == c) or (g.vs[e.target]["community"] == c))
    external = total - internal
    print(f"  Community {c}: {internal} internal, {external} external edges")

print("\nAverage Clustering Coefficient per Community:")
for c, _ in comm_counts.most_common(10):
    nodes_in_comm = [v.index for v in g.vs if v['community'] == c]
    subgraph = g.subgraph(nodes_in_comm)
    avg_clust = subgraph.transitivity_avglocal_undirected()
    print(f"Community {c}: {avg_clust}")

print("\n=== STRUCTURAL FEATURES ===")
# Clustering coefficient (transitivity)
print(f"Average clustering coefficient: {g.transitivity_undirected():.4f}")

plt.show()

