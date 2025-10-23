import igraph as ig
from collections import defaultdict
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
# Calculate communities using the Louvain algorithm
partition = g.community_multilevel(weights=g.es["weight"])

# Assign community membership to vertices
g.vs['community'] = partition.membership

#print the number of communities found
print(f"Number of communities found: {len(partition)}")


# Save nodes, with community to CSV
nodes_df = pd.DataFrame({
    'Id': g.vs['name'],
    'Community': g.vs['community'],
})
nodes_df.to_csv("coretweet_nodes_with_communities.csv", index=False)

# Load the full tweets data to get user details
tweets_df = pd.read_csv("tweets.csv")
tweets_df = tweets_df[tweets_df['reference_type'] == 'retweeted'].copy()

# Convert IDs to strings for consistency
tweets_df['retweet_author_id'] = tweets_df['retweet_author_id'].astype(str)
nodes_df['Id'] = nodes_df['Id'].astype(str)

# Keep the row with highest retweet_count per user
user_details_df = tweets_df.sort_values('retweet_count', ascending=False)\
                            .drop_duplicates('retweet_author_id')

# Select only needed columns and rename for clarity
user_details_df = user_details_df[['retweet_author_id', 'retweeted_screen_name', 'text', 'created_at']]
user_details_df = user_details_df.rename(columns={
    'retweet_author_id': 'Id',
    'retweet_screen_name': 'Name',
    'text': 'Text',
    'created_at': 'Time'
})

# Merge node info with user details
output_df = nodes_df.merge(user_details_df, on='Id', how='left')

# Save final CSV
output_df.to_csv("coretweet_nodes_with_communities_and_details.csv", index=False)


