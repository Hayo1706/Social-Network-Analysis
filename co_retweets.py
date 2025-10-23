import pandas as pd

from collections import defaultdict
from itertools import combinations


# === Step 1. Load data efficiently ===
csv_file = "tweets.csv"

use_cols = ["author_id", "retweet_author_id", "reference_type"]
df = pd.read_csv(csv_file, low_memory=False, usecols=use_cols)

# Get users with the highest number of retweets
df = df[df['reference_type'] == 'retweeted'].copy()
tweet_groups = df.groupby('retweet_author_id')['author_id'].apply(list)
tweet_groups = tweet_groups.sort_values(key=lambda x: x.str.len(), ascending=False)
top = tweet_groups.head(1500)

# Build an inverted index: retweeter -> set of authors they retweeted
retweeter_to_authors = defaultdict(set)
for author, retweeters in top.items():
    for r in retweeters:
        retweeter_to_authors[r].add(author)

# Now count co-retweets between authors efficiently
edge_weights = defaultdict(int)

for retweeter, authors in retweeter_to_authors.items():
    authors = list(authors)
    for a1, a2 in combinations(sorted(authors), 2):
        edge_weights[(a1, a2)] += 1

# Convert to DataFrame
edges_df = pd.DataFrame([
    {'source': a1, 'target': a2, 'weight': w}
    for (a1, a2), w in edge_weights.items()
])
edges_df.to_csv("coretweet_edges.csv", index=False)

print("done")