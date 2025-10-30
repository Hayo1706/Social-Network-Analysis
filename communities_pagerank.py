import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import sys
import numpy as np

# --- Configuration ---
NODE_FILE = "coretweet_nodes_with_communities_and_details.csv"
EDGE_FILE = "coretweet_edges.csv"

def full_analysis_and_visualization():

    # --- 1. Load Node Data ---
    print(f"Loading node details from {NODE_FILE}...")
    nodes_df = pd.read_csv(NODE_FILE)

    # --- 2. Load Edge Data ---
    print(f"Loading edge list from {EDGE_FILE}...")
    edges_df = pd.read_csv(EDGE_FILE)

    # --- 3. Build Graph with NetworkX ---
    print("Building graph...")
    G = nx.Graph()

    edges_df['source'] = edges_df['source'].astype(str)
    edges_df['target'] = edges_df['target'].astype(str)
    G.add_weighted_edges_from(edges_df[['source', 'target', 'weight']].values)

    nodes_df['Id'] = nodes_df['Id'].astype(str)
    nodes_df = nodes_df.set_index('Id')

    nodes_to_add = set(G.nodes()) & set(nodes_df.index)
    
    # Use .to_dict() for fast attribute setting
    for column in nodes_df.columns:
        # Ensure we only add attributes for nodes that exist in the graph
        attr_dict = pd.Series(nodes_df[column], index=nodes_to_add).to_dict()
        nx.set_node_attributes(G, attr_dict, name=column)

    print(f"Graph created with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    
    # --- 4. Calculate Centrality Measures ---
    print("Calculating centrality measures")

    # a) Weighted Degree (Strength)
    print("Calculating Weighted Degree (Strength)...")
    strength = dict(G.degree(weight='weight'))
    nx.set_node_attributes(G, strength, 'Weighted_Degree_Strength')

    # b) PageRank
    print("Calculating PageRank...")
    pagerank = nx.pagerank(G, weight='weight')
    nx.set_node_attributes(G, pagerank, 'PageRank')

    # c) Betweenness Centrality
    print("Calculating Betweenness Centrality")
    edges_df['distance'] = 1.0 / edges_df['weight']
    G_with_distance = nx.Graph()
    G_with_distance.add_weighted_edges_from(edges_df[['source', 'target', 'distance']].values, weight='distance')
    betweenness = nx.betweenness_centrality(G_with_distance, weight='distance', normalized=True)
    nx.set_node_attributes(G, betweenness, 'Betweenness')

    print("Centrality calculations complete.")

    # --- 5. Finalize and Save Output to CSV ---
    print("Saving centrality results to coretweet_nodes_with_centrality.csv")
    
    centrality_df = pd.DataFrame({
        'Id': list(strength.keys()),
        'Weighted_Degree_Strength': list(strength.values()),
        'PageRank': [pagerank.get(n, 0) for n in strength.keys()],
        'Betweenness': [betweenness.get(n, 0) for n in strength.keys()]
    }).set_index('Id')

    final_output_df = nodes_df.merge(
        centrality_df,
        left_index=True,
        right_index=True,
        how='left'
    ).reset_index().rename(columns={'index': 'Id'})

    final_output_df = final_output_df.sort_values(by='PageRank', ascending=False)
    
    centrality_cols = ['Weighted_Degree_Strength', 'PageRank', 'Betweenness']
    final_output_df[centrality_cols] = final_output_df[centrality_cols].fillna(0)

    final_output_df.to_csv("coretweet_nodes_with_centrality.csv", index=False, encoding='utf-8')
    
    print("Successfully saved CSV file.")

    # --- 6. Prepare for Visualization ---
    print("Preparing visualization data (colors, sizes)...")
    
    # We will only draw the largest connected component to make it cleaner
    largest_cc = max(nx.connected_components(G), key=len)
    G_sub = G.subgraph(largest_cc)
    print(f"Visualizing the largest connected component with {G_sub.number_of_nodes()} nodes.")

    # Get node attributes from the subgraph
    # We already calculated these and set them on the graph
    pagerank_values = nx.get_node_attributes(G_sub, 'PageRank')
    community_values = nx.get_node_attributes(G_sub, 'Community')
    
    # Handle potential missing community data if some nodes weren't in the original nodes_df
    # but were in the edge list
    default_community = -1 # Assign a default community for 'orphaned' nodes
    community_values = {
        node: community_values.get(node, default_community) 
        for node in G_sub.nodes()
    }

    # a) Set up Node Colors based on Community
    all_colors = list(mcolors.TABLEAU_COLORS.values())
    unique_communities = sorted(list(set(community_values.values())))
    color_map = {comm: all_colors[i % len(all_colors)] for i, comm in enumerate(unique_communities)}
    # Assign black color for the default/unknown community
    color_map[default_community] = '#000000' 
    
    node_colors = [color_map[community_values[node]] for node in G_sub.nodes()]

    # b) Set up Node Sizes based on PageRank
    min_size = 10
    max_size = 2000
    
    pr_values = [pagerank_values.get(node, 0) for node in G_sub.nodes()]
    min_pr = min(pr_values)
    max_pr = max(pr_values)
    
    node_sizes = [min_size + (pr - min_pr) * (max_size - min_size) / (max_pr - min_pr) if (max_pr - min_pr) > 0 else min_size for pr in pr_values]

    # --- 7. Draw the Graph ---
    print("Drawing graph (this may take a few minutes for a large graph)...")
    
    plt.figure(figsize=(20, 20))
    
    pos = nx.spring_layout(G_sub, k=0.1, iterations=50, seed=42)

    nx.draw_networkx(
        G_sub,
        pos=pos,
        node_color=node_colors,
        node_size=node_sizes,
        with_labels=False,
        width=0.1,
        alpha=0.7
    )

    plt.title("Co-Retweet Network Visualization (Sized by PageRank, Colored by Community)", fontsize=30)
    plt.axis('off')
    
    plt.savefig("network_visualization.png", format="PNG", dpi=300, bbox_inches='tight')
    
    print("\n--- Pipeline Complete ---")
    print(f"Successfully saved visualization to network_visualization.png")

    # --- 8. Print Console Reports ---
    print("\n--- Top 10 Most Influential Users (by PageRank) ---")
    print(final_output_df[['retweeted_screen_name', 'PageRank', 'Weighted_Degree_Strength']].head(10))


if __name__ == "__main__":
    full_analysis_and_visualization()


