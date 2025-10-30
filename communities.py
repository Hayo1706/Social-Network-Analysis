import os
from pathlib import Path
import pandas as pd
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
# Communities.py
# Read nodes CSV, count communities, and visualize network with differently coloured communities using networkx


DATA_DIR = Path(__file__).parent
NODES_FILE = DATA_DIR / "coretweet_nodes_with_communities_and_details.csv"

def choose_column(cols, candidates):
    lc = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lc:
            return lc[cand.lower()]
    return None

def try_read_edges():
    # common edge filenames to try
    candidates = [
        "coretweet_edges.csv",
        "coretweet_edges_with_details.csv",
        "coretweet_edgelist.csv",
        "edges.csv",
        "edgelist.csv",
        "links.csv",
    ]
    for fname in candidates:
        p = DATA_DIR / fname
        if p.exists():
            try:
                return pd.read_csv(p)
            except Exception:
                continue
    return None

def main():
    if not NODES_FILE.exists():
        raise FileNotFoundError(f"Nodes file not found: {NODES_FILE}")

    df = pd.read_csv(NODES_FILE)
    if df.empty:
        raise SystemExit("Nodes file is empty")

    # Detect node id and community columns heuristically
    id_col = choose_column(df.columns, ["id", "node", "node_id", "user_id", "screen_name", "username", "label", "name"])
    comm_col = choose_column(df.columns, ["community", "community_id", "community_label", "modularity_class", "cluster", "group"])

    if id_col is None:
        # fallback: use the first column as id
        id_col = df.columns[0]

    if comm_col is None:
        raise SystemExit("Could not find a community column in the nodes CSV. Expected columns like 'community', 'community_id', or 'modularity_class'.")

    # Ensure node ids are strings (safe for NetworkX)
    df[id_col] = df[id_col].astype(str)
    df[comm_col] = df[comm_col].astype(str)

    # Count unique communities and print
    unique_comms = sorted(df[comm_col].unique())
    n_communities = len(unique_comms)
    print(f"Found {n_communities} communities")

    # Build graph
    G = nx.Graph()
    for _, row in df.iterrows():
        node = row[id_col]
        # keep community as attribute
        G.add_node(node, **{comm_col: row[comm_col]})
        # copy other useful attributes (optional)
        for c in df.columns:
            if c not in (id_col,):
                G.nodes[node][c] = row[c]

    # Try to load an edges file (common names). If found, add edges.
    edges_df = try_read_edges()
    if edges_df is not None:
        # detect source/target columns
        src_col = choose_column(edges_df.columns, ["source", "src", "from", "u", "node1", "source_id"])
        tgt_col = choose_column(edges_df.columns, ["target", "tgt", "to", "v", "node2", "target_id"])
        if src_col is None or tgt_col is None:
            # if only two unnamed columns, use them
            if len(edges_df.columns) >= 2:
                src_col, tgt_col = edges_df.columns[0], edges_df.columns[1]
            else:
                src_col = tgt_col = None

        if src_col and tgt_col:
            # coerce to strings to match node ids
            for _, erow in edges_df.iterrows():
                s = str(erow[src_col])
                t = str(erow[tgt_col])
                G.add_edge(s, t)
            print(f"Loaded edges from file. Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
        else:
            print("Edges file found but could not detect source/target columns. Proceeding with nodes-only graph.")
    else:
        print("No edges file found. Visualizing nodes-only network (no edges).")

    # Prepare coloring by community
    communities = [G.nodes[n].get(comm_col, "None") for n in G.nodes()]
    cat = pd.Categorical(communities, categories=unique_comms)
    color_idx = cat.codes  # integers 0..k-1

    # choose colormap with enough distinct colors
    cmap = cm.get_cmap("tab20", max(3, n_communities))
    node_colors = [cmap(i % cmap.N) for i in color_idx]

    # layout
    if G.number_of_edges() > 0:
        pos = nx.forceatlas2_layout(G, max_iter=800, scaling_ratio=1, seed=42)
    else:
        pos = nx.circular_layout(G)

    plt.figure(figsize=(14, 10))
    # draw edges lightly
    if G.number_of_edges() > 0:
        nx.draw_networkx_edges(G, pos, alpha=0.3, width=0.6)

    # draw nodes (size scaled by degree if edges exist)
    if G.number_of_edges() > 0:
        degrees = np.array([d for _, d in G.degree()])
        dmin, dmax = degrees.min(), degrees.max()
        max_size = 300
        min_size = 20
        node_sizes = min_size + (degrees - dmin) * (max_size - min_size) / (dmax - dmin)

        nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors="black", linewidths=0.3)
        nx.draw_networkx_edges(G, pos, alpha=0.01, width=0.01, edge_color='red')
    else:
        nx.draw_networkx_nodes(G, pos, node_size=80, node_color=node_colors)

    # optional labels when graph is small
    if G.number_of_nodes() <= 50:
        nx.draw_networkx_labels(G, pos, font_size=8)

    plt.title(f"The {n_communities} Communities of Co-Retweet Network")
    plt.axis("off")

    # legend: map community labels to colors (show up to 25)
    if n_communities <= 25:
        import matplotlib.patches as mpatches
        patches = []
        for i, comm in enumerate(unique_comms):
            patches.append(mpatches.Patch(color=cmap(i % cmap.N), label=str(comm)))
        plt.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc="upper left", title="Community")

    out_png = DATA_DIR / "communities_visualization.png"
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    print(f"Saved visualization to: {out_png}")
    plt.show()

if __name__ == "__main__":
    main()

    # scale down plotted nodes and add a thin black outline for improved readability,
    # then re-save the figure (works on the last-created matplotlib figure)
    import matplotlib.collections as mcoll
    import matplotlib.pyplot as plt

    fig = plt.gcf()
    SCALE_FACTOR = 0.2  # reduce node marker size to 35% of original
    LINEWIDTH = 0.6
    EDGE_COLOR = "black"

    modified = False
    for ax in fig.axes:
        for coll in list(ax.collections):
            if isinstance(coll, mcoll.PathCollection):
                sizes = coll.get_sizes()
                if sizes is None or len(sizes) == 0:
                    continue
                try:
                    coll.set_sizes(sizes * SCALE_FACTOR)
                    coll.set_edgecolors(EDGE_COLOR)
                    coll.set_linewidths(LINEWIDTH)
                    modified = True
                except Exception:
                    # skip collections that don't support these changes
                    continue

    if modified:
        out_png = Path(__file__).parent / "communities_visualization_outlined.png"
        plt.tight_layout()
        plt.savefig(out_png, dpi=200)
        print(f"Saved outlined visualization to: {out_png}")
        plt.show()
    else:
        print("No node collections found to adjust.")