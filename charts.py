import networkx as nx
import matplotlib.pyplot as plt

# Create a directed graph
G = nx.DiGraph()

# Define the nodes and edges for the task "Cut the Apple"
nodes = [
    "Start",
    "Detect Apple",
    "Grip Apple",
    "Verify Grip",
    "Position Knife",
    "Verify Alignment",
    "Cut Apple",
    "Confirm Slice",
    "End"
]

edges = [
    ("Start", "Detect Apple"),
    ("Detect Apple", "Grip Apple"),
    ("Grip Apple", "Verify Grip"),
    ("Verify Grip", "Position Knife"),
    ("Position Knife", "Verify Alignment"),
    ("Verify Alignment", "Cut Apple"),
    ("Cut Apple", "Confirm Slice"),
    ("Confirm Slice", "End")
]

# Add nodes and edges to the graph
G.add_nodes_from(nodes)
G.add_edges_from(edges)

# Create the layout for the graph
pos = nx.spring_layout(G, seed=42)

# Plot the graph
plt.figure(figsize=(10, 6))
nx.draw_networkx_nodes(G, pos, node_color="lightblue", node_size=2000)
nx.draw_networkx_edges(G, pos, edgelist=edges, arrowstyle="->", arrowsize=20, edge_color="gray")
nx.draw_networkx_labels(G, pos, font_size=10, font_weight="bold")

# Add the title
plt.title("GOMS Model: Task Decomposition for 'Cut the Apple'", fontsize=14)
plt.axis("off")
plt.show()
