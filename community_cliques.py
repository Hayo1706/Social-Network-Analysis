import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import os

# --- 1. Load Data ---
df = pd.read_csv("coretweet_nodes_with_communities_and_details.csv")

# --- 2. Build Graph ---
G = nx.Graph()

# Add edges between user and retweeted_screen_name
for _, row in df.iterrows():
    if pd.notna(row['retweeted_screen_name']):
        G.add_edge(row['Id'], row['retweeted_screen_name'], community=row['Community'])

# --- 3. Prepare output directory ---
output_dir = "community_clique_images"
os.makedirs(output_dir, exist_ok=True)

# --- 4. Analyze each community and save images ---
communities = df['Community'].unique()

for community in communities:
    print(f"\n=== Community {community} ===")
    
    # Extract nodes in this community
    community_nodes = set(df[df['Community'] == community]['Id'])
    subG = G.subgraph(community_nodes | {n for u, v in G.edges() for n in (u, v)
                                         if u in community_nodes or v in community_nodes})
    
    # Find cliques
    cliques = list(nx.find_cliques(subG))
    cliques_sorted = sorted(cliques, key=len, reverse=True)
    
    print(f"Number of cliques: {len(cliques_sorted)}")
    if cliques_sorted:
        print(f"Largest clique (size {len(cliques_sorted[0])}): {cliques_sorted[0]}")
    
    # --- 5. Visualize and Save ---
    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(subG, seed=42)
    
    # Highlight nodes in largest clique
    largest_clique = set(cliques_sorted[0]) if cliques_sorted else set()
    node_colors = ['red' if node in largest_clique else 'skyblue' for node in subG.nodes()]
    
    nx.draw_networkx(subG, pos,
                     with_labels=False,
                     node_color=node_colors,
                     node_size=80,
                     edge_color='gray',
                     alpha=0.7)
    
    plt.title(f"Community {community} - Largest Clique Highlighted")
    plt.axis('off')
    
    # Save the figure
    file_path = os.path.join(output_dir, f"community_{community}_cliques.png")
    plt.savefig(file_path, bbox_inches='tight', dpi=300)
    plt.close()
    
    print(f"Saved clique visualization for community {community} to {file_path}")
