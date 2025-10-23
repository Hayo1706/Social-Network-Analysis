import igraph as ig

import pandas as pd


# Load the co-retweet edges
edges_df = pd.read_csv("coretweet_edges.csv")
print(edges_df.info())
print(edges_df.head())
# Create the graph
g = ig.Graph.DataFrame(
    edges_df,
    directed=False,
    vertices=None,           # infer vertices automatically
    use_vids=False,          # treat source/target as labels
)
# Calculate communities using the Leiden algorithm
partition = g.community_multilevel(weights=g.es["weight"])
# partition = g.community_leiden(weights=g.es["weight"], resolution=0.1)
# Assign community membership to vertices
g.vs['community'] = partition.membership

#print the number of communities found
print(f"Number of communities found: {len(partition)}")
print()
