import igraph as ig
import pandas as pd
import pycountry
from pycountry_convert import country_alpha2_to_continent_code, country_name_to_country_alpha2

NODE_FILE = "coretweet_nodes_with_communities_and_more_details.csv"
EDGE_FILE = "coretweet_edges.csv"

# --- Continent Mapping ---
CONTINENT_MAP = {
    'NA': 'North America',
    'SA': 'South America',
    'AS': 'Asia',
    'AF': 'Africa',
    'OC': 'Oceania',
    'EU': 'Europe',
    'AN': 'Antarctica'
}

MANUAL_MAP = {
    # North America
    'usa': 'NA', 'united states': 'NA', 'us': 'NA', 'nyc': 'NA', 'new york': 'NA', 'sf': 'NA', 
    'ca': 'NA', 'la': 'NA', 'washington dc': 'NA', 'dc': 'NA', 'chicago': 'NA',
    'canada': 'NA', 'toronto': 'NA', 'vancouver': 'NA', 'montreal': 'NA',
    'mexico': 'NA', 'los angeles, ca': 'NA', 'texas, usa': 'NA', 'washington, dc': 'NA',
    'new york, usa': 'NA', 'florida': 'NA', 'toronto, ontario': 'NA',
    'brooklyn, ny': 'NA', 'california, usa': 'NA', 'new york, ny': 'NA',
    'portland, or': 'NA', 'north carolina, usa': 'NA', 'san francisco, ca': 'NA',
    'northern california': 'NA', 'baltimore, md': 'NA', 'mississauga, ontario': 'NA',
    'san jose, ca': 'NA', 'philadelphia': 'NA', 'san diego': 'NA',
    'philadelphia, pa': 'NA', 'stolen ohlone land': 'NA', 'california': 'NA', 'minnesota, usa': 'NA', 'manhattan, ny': 'NA',
    'madison, wi': 'NA', 'halifax, nova scotia': 'NA', 'kingston': 'NA', 'massachusetts, usa': 'NA', 'missouri, usa': 'NA',
    'chicago, il': 'NA', 'tennessee, usa': 'NA', 'kansas city, mo': 'NA',
    'arizona, usa': 'NA', 'newark, nj': 'NA', 'calgary, alberta': 'NA',
    'orlando, fl': 'NA', 'san diego, ca': 'NA', '🇯🇲': 'NA', 'atlanta, usa': 'NA',
    
    # Europe
    'uk': 'EU', 'united kingdom': 'EU', 'london': 'EU', 'england': 'EU', 'scotland': 'EU', 
    'ireland': 'EU', 'dublin': 'EU',
    'germany': 'EU', 'berlin': 'EU',
    'france': 'EU', 'paris': 'EU',
    'spain': 'EU', 'madrid': 'EU', 'barcelona': 'EU',
    'italy': 'EU', 'rome': 'EU',
    'netherlands': 'EU', 'amsterdam': 'EU',
    'london, england': 'EU',
    'glasgow, scotland': 'EU',
    'oxfordshire great britain': 'EU',
    'birmingham, england': 'EU',
    'isle of wight': 'EU',
    'aberdeen, scotland': 'EU',
    'brussels': 'EU',
    'south west, england': 'EU',
    'north east, england': 'EU',
    'best market town n yorks': 'EU',
    'sussex, uk': 'EU',
    'hingland': 'EU',
    
    # Asia
    'india': 'AS', 'mumbai': 'AS', 'delhi': 'AS', 'bangalore': 'AS',
    'japan': 'AS', 'tokyo': 'AS',
    'singapore': 'AS',
    'indonesia': 'AS', 'jakarta': 'AS',
    'china': 'AS', 'beijing': 'AS', 'shanghai': 'AS',
    'philippines': 'AS',
    'hindistan': 'AS', 
    'bharat': 'AS',
    'भारत': 'AS',
    'chennai': 'AS',
    'hyderabad': 'AS',
    'patna': 'AS',
    'ph': 'AS',
    'new delhi': 'AS',
    'kuala lumpur city, kuala lumpur federal territory': 'AS',
    'mas': 'AS',
    'honnvara': 'AS', 
    'bangalore | madhubani': 'AS',
    'ब्रज भूमि': 'AS',
    
    # South America
    'brasil': 'SA', 'brazil': 'SA', 'sao paulo': 'SA', 'rio de janeiro': 'SA',
    'argentina': 'SA', 'buenos aires': 'SA',
    
    # Africa
    'nigeria': 'AF', 'lagos': 'AF',
    'south africa': 'AF', 'johannesburg': 'AF', 'cape town': 'AF',
    'kenya': 'AF', 'nairobi': 'AF',
    'kumasi': 'AF',
    'aflao - volta region': 'AF', 
    
    # Oceania
    'australia': 'OC', 'sydney': 'OC', 'melbourne': 'OC',
    'new zealand': 'OC',
    'melbourne, victoria': 'OC',
    
    # Misc 
    'global': 'Unknown', 'earth': 'Unknown', 'worldwide': 'Unknown', 'planet earth': 'Unknown',
    '#': 'Unknown',
    'where i need to be': 'Unknown',
    'everywhere': 'Unknown',
    'bil kul risk nahi lene ka': 'Unknown',
    'on the streets with no names': 'Unknown',
    'centre of the universe': 'Unknown',
    '@dontmesswithtruth': 'Unknown',
    'iron throne': 'Unknown',
    'out & about ωψφ': 'Unknown',
    'underground': 'Unknown',
    'प्रभु चरण': 'Unknown',
    '/etc/hosts': 'Unknown',
}

# Pre-compile a list of country names for searching
try:
    COUNTRY_NAMES = [country.name.lower() for country in pycountry.countries]
except Exception as e:
    print(f"Warning: Could not load pycountry.countries list: {e}")
    COUNTRY_NAMES = []


def clean_location(loc):
    if pd.isna(loc):
        return "unknown"
    try:
        return str(loc).strip().lower()
    except Exception:
        return "unknown"

def map_location_to_continent(location_str):
    if not location_str or location_str == "unknown":
        return "Unknown"

    # 1. Check manual map first
    if location_str in MANUAL_MAP:
        return CONTINENT_MAP.get(MANUAL_MAP[location_str], "Unknown")

    # 2. Try to convert the *whole string* as a country name
    try:
        alpha2 = country_name_to_country_alpha2(location_str, cn_name_format="lower")
        continent_code = country_alpha2_to_continent_code(alpha2)
        return CONTINENT_MAP.get(continent_code, "Unknown")
    except Exception:
        pass 

    # 3. Try to find a known country name *within* the string (e.g., "Paris, France")
    for country_name in COUNTRY_NAMES:
        if country_name in location_str:
            try:
                alpha2 = country_name_to_country_alpha2(country_name, cn_name_format="lower")
                continent_code = country_alpha2_to_continent_code(alpha2)
                return CONTINENT_MAP.get(continent_code, "Unknown")
            except Exception:
                continue
    
    # 4. If all else fails
    return "Unknown"


def analyze_homophily():
    # --- 1. Load Data ---
    nodes_df = pd.read_csv(NODE_FILE)
    edges_df = pd.read_csv(EDGE_FILE)

    # --- 2. Clean and Prepare Data (MOVED UP) ---
    

    nodes_df['Id'] = nodes_df['Id'].astype(str)
    edges_df['source'] = edges_df['source'].astype(str)
    edges_df['target'] = edges_df['target'].astype(str)
        
    original_rows = len(nodes_df)
    nodes_df = nodes_df.drop_duplicates(subset=['Id'], keep='first')
    dropped_rows = original_rows - len(nodes_df)
    if dropped_rows > 0:
        print(f"Warning: Removed {dropped_rows} duplicate node entries from {NODE_FILE}.")

    print(f"Loaded {len(nodes_df)} unique nodes and {len(edges_df)} edges.")

    # --- Map locations to continents ---
    print("Mapping locations to continents... (This may take a moment)")
    nodes_df['clean_location'] = nodes_df["Location"].apply(clean_location)
    nodes_df['Continent'] = nodes_df['clean_location'].apply(map_location_to_continent)
    
    # Convert string continents to unique integer IDs for assortativity
    unique_continents = sorted(list(nodes_df['Continent'].unique()))
    continent_to_id = {cont: i for i, cont in enumerate(unique_continents)}
    nodes_df['continent_id'] = nodes_df['Continent'].map(continent_to_id)

    # --- Add this block to inspect continent data ---
    print("\n--- Continent Mapping Results ---")
    print(nodes_df['Continent'].value_counts())
    print("-----------------------------------")
    
    # --- Add this block to inspect *unknown* locations ---
    unknown_nodes = nodes_df[nodes_df['Continent'] == 'Unknown']
    if not unknown_nodes.empty:
        print("\n--- Top 30 UNKNOWN Locations ---")
        print(unknown_nodes['clean_location'].value_counts().head(30))
        print("---------------------------------------------------------")


    nodes_df = nodes_df.set_index('Id')

    # --- 3. Build the Graph ---
    try:
        g = ig.Graph.DataFrame(
            edges_df,
            directed=False,
            use_vids=False
        )
    except Exception as e:
        print(f"Error creating graph from edge list: {e}")
        edge_ids = set(edges_df['source']).union(set(edges_df['target']))
        node_ids = set(nodes_df.index)
        missing_ids = edge_ids - node_ids
        if missing_ids:
            print(f"Found {len(missing_ids)} IDs in the edge file that are not in the node file (these nodes will have no attributes).")
            print(f"Example missing IDs: {list(missing_ids)[:5]}")
        pass

    print(f"Graph structure created with {g.vcount()} vertices and {g.ecount()} edges.")

    # --- 4. Add Node Attributes ---

    attributes_to_add = ["Location", "Community", 'Continent', 'continent_id']
    
    missing_cols = [col for col in attributes_to_add if col not in nodes_df.columns and col not in ['Continent', 'continent_id']]
    if missing_cols:
        print(f"Error: The node file {NODE_FILE} is missing required columns: {missing_cols}")
        return
        
    try:
        nodes_df_attrs = nodes_df[attributes_to_add]
        nodes_df_dict = nodes_df_attrs.to_dict('index')
    except KeyError as e:
        print(f"Error: A required column is missing from {NODE_FILE}. {e}")
        return

    v_attrs = {col: [] for col in attributes_to_add}
    v_attrs_found = 0
    
    # --- Get the ID for 'Unknown' continent ---
    unknown_continent_id = continent_to_id.get("Unknown", -1)

    for v in g.vs:
        v_name = v['name']
        v_data = nodes_df_dict.get(v_name)
        
        if v_data:
            v_attrs_found += 1
            for col in attributes_to_add:
                v_attrs[col].append(v_data[col])
        else:
            # This vertex was in the edge list but not the node list.
            # --- Assign default continent values ---
            v_attrs["Location"].append(None)
            v_attrs["Community"].append(-1) # BUGFIX: Was -I, now -1
            v_attrs['Continent'].append("Unknown")
            v_attrs['continent_id'].append(unknown_continent_id)
            
    for col, values in v_attrs.items():
        g.vs[col] = values
        
    if v_attrs_found < g.vcount():
        print(f"Warning: Assigned attributes to {v_attrs_found} / {g.vcount()} vertices.")
        print(f"  {g.vcount() - v_attrs_found} vertices were in the edge file but not the node file.")
    else:
        print(f"Successfully assigned attributes to all {g.vcount()} vertices.")


    # --- 5. Handle "Unknown" Continents ---
    
    unknown_id = continent_to_id.get("Unknown", -1)
    
    if unknown_id == -1:
        print("No 'Unknown' continents found to filter.")
        known_nodes_count = g.vcount()
        total_nodes_count = g.vcount()
        g_known = g 
    else:
        # Select vertices that *do not* have the unknown_id
        known_nodes = g.vs.select(continent_id_ne=unknown_id)
        known_nodes_count = len(known_nodes)
        total_nodes_count = g.vcount()
        g_known = g.subgraph(known_nodes)
    
    if total_nodes_count == 0:
        print("Error: Graph has zero nodes.")
        return

    percent_known = (known_nodes_count / total_nodes_count) * 100
    print(f"\n--- Continent Data Quality ---")
    print(f"{known_nodes_count} / {total_nodes_count} nodes ({percent_known:.1f}%) have a known continent.")

    if unknown_id != -1:
        print(f"Analysis will run on subgraph of {g_known.vcount()} nodes and {g_known.ecount()} edges.")

    # --- 6. Method 1: Calculate Assortativity ---
    print("\n--- Analysis Results ---")
    assortativity_val = g_known.assortativity_nominal(
        types=g_known.vs['continent_id'], 
        directed=False
    )
    print(f"Continent Assortativity Coefficient (r): {assortativity_val:.4f}")

    # --- 7. Method 2: Calculate E-I Index ---
    internal_edges = 0
    external_edges = 0
    
    for edge in g_known.es:
        source_node = g_known.vs[edge.source]
        target_node = g_known.vs[edge.target]
        
        try:
            weight = edge["weight"]
        except KeyError:
            weight = 1
        
        # --- UPDATED: Use continent_id ---
        if source_node['continent_id'] == target_node['continent_id']:
            internal_edges += weight
        else:
            external_edges += weight
            
    total_edges = internal_edges + external_edges
    
    if total_edges > 0:
        ei_index = (external_edges - internal_edges) / total_edges
        print(f"\nE-I Index (Continent): {ei_index:.4f}")
        print(f"  Internal edge weight: {internal_edges}")
        print(f"  External edge weight: {external_edges}")

    # --- 8. Sanity Check: Community Homophily ---
    if "Community" in g.vs.attributes():
        community_assortativity = g.assortativity_nominal(
            types=g.vs["Community"], 
            directed=False
        )
        print(f"\n--- Sanity Check ---")
        print(f"Community Assortativity: {community_assortativity:.4f}")

if __name__ == "__main__":
    analyze_homophily()