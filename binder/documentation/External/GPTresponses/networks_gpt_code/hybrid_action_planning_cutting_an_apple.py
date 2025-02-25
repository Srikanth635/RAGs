import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout

# Create a directed graph
G = nx.DiGraph()

# Define nodes (steps in hybrid action planning)
nodes = [
    "Perception",
    "Object Detection",
    "Symbolic Reasoning",
    "ML Data Processing",
    "Path Planning",
    "Grasp Planning",
    "Cutting Motion",
    "Error Handling",
    "Execute Task",
    "Outcome: Apple Cut",
    "Outcome: Error Detected",
    "Outcome: Slicing Complete",
    "Outcome: Cutting Complete",
    "Outcome: Dicing Complete"
]

# Add nodes to the graph
G.add_nodes_from(nodes)

# Define edges (dependencies and flow between steps)
edges = [
    ("Perception", "Object Detection"),
    ("Object Detection", "Symbolic Reasoning"),
    ("Object Detection", "ML Data Processing"),
    ("Symbolic Reasoning", "Path Planning"),
    ("ML Data Processing", "Path Planning"),
    ("Path Planning", "Grasp Planning"),
    ("Grasp Planning", "Cutting Motion"),
    ("Cutting Motion", "Execute Task"),
    ("Execute Task", "Outcome: Apple Cut"),
    ("Execute Task", "Outcome: Slicing Complete"),
    ("Execute Task", "Outcome: Cutting Complete"),
    ("Execute Task", "Outcome: Dicing Complete"),
    ("Execute Task", "Error Handling"),
    ("Error Handling", "Outcome: Error Detected"),
    ("Error Handling", "Perception")
]

# Add edges to the graph
G.add_edges_from(edges)

# Add new nodes for error feedback mechanisms
error_mechanisms = [
    "Error: Sensor Failure",
    "Error: Object Misalignment",
    "Error: Tool Damage",
    "Retry Task"
]

# Add error-related nodes to the graph
G.add_nodes_from(error_mechanisms)

# Define edges for error feedback mechanisms
error_edges = [
    ("Error Handling", "Error: Sensor Failure"),
    ("Error Handling", "Error: Object Misalignment"),
    ("Error Handling", "Error: Tool Damage"),
    ("Error: Sensor Failure", "Retry Task"),
    ("Error: Object Misalignment", "Retry Task"),
    ("Error: Tool Damage", "Retry Task"),
    ("Retry Task", "Perception")
]

# Add error-related edges to the graph
G.add_edges_from(error_edges)

# Generate a hierarchical layout using Graphviz
pos = graphviz_layout(G, prog="dot")

# Plot the graph
plt.figure(figsize=(16, 12))

# Draw all nodes
nx.draw(
    G, pos, with_labels=True, node_color="skyblue", node_size=2000, font_size=9, font_weight="bold", edge_color="gray"
)

# Highlight the first step node (Perception) with a distinct color
nx.draw_networkx_nodes(G, pos, nodelist=["Perception"], node_color="gold")

# Highlight key outcomes
nx.draw_networkx_nodes(
    G,
    pos,
    nodelist=[
        "Outcome: Apple Cut",
        "Outcome: Error Detected",
        "Outcome: Slicing Complete",
        "Outcome: Cutting Complete",
        "Outcome: Dicing Complete"
    ],
    node_color="lightgreen"
)

# Highlight other important steps and retry mechanisms
nx.draw_networkx_nodes(G, pos, nodelist=["Execute Task", "Retry Task"], node_color="lightcoral")

# Highlight error nodes
nx.draw_networkx_nodes(G, pos, nodelist=error_mechanisms, node_color="orange")

# Add a title
plt.title("Refined Hybrid Action Planning Network with Hierarchical Layout", fontsize=14)

plt.show()
