import matplotlib.pyplot as plt
import networkx as nx

# Create a directed graph for the specific task of cutting an apple
G_cutting = nx.DiGraph()

# Define nodes and edges for cutting an apple task
cutting_nodes = {
    "Cutting Action Model for Manipulation": [
        "Preconditions",
        "Actions",
        "Postconditions/Outcomes",
        "Feedback Loops",
        "Task-Specific Variations"
    ],
    "Preconditions": [
        "Apple is stable",
        "Knife is sharp",
        "Proper grip on knife and apple",
        "Workspace is clear"
    ],
    "Actions": [
        "Stabilize apple",
        "Position knife",
        "Apply force",
        "Execute cutting motion"
    ],
    "Postconditions/Outcomes": [
        "Apple is cut into pieces",
        "Knife returned to rest position",
        "Workspace is clean or needs cleanup"
    ],
    "Feedback Loops": [
        "Adjust force based on resistance",
        "Realign knife if motion deviates",
        "Detect completion of cut visually or via force feedback"
    ],
    "Task-Specific Variations": [
        "Cut size variation (e.g., slices or chunks)",
        "Different apple sizes or shapes",
        "Handling slippery surface",
        "One-handed operation support"
    ]
}

# Add nodes and edges to the graph
for parent, children in cutting_nodes.items():
    for child in children:
        G_cutting.add_edge(parent, child)

# Draw the network for cutting an apple task
plt.figure(figsize=(16, 10))
pos_cutting = nx.spring_layout(G_cutting, seed=42, k=0.8)  # Spring layout for better visualization
nx.draw_networkx_nodes(G_cutting, pos_cutting, node_size=2000, node_color="lightgreen")
nx.draw_networkx_edges(G_cutting, pos_cutting, arrows=True, arrowstyle="->", edge_color="gray", alpha=0.7)
nx.draw_networkx_labels(G_cutting, pos_cutting, font_size=10, font_color="black")

# Adding a title to indicate the model applied
plt.title("Cutting Action Model for Manipulation - Cutting an Apple", fontsize=16)
plt.axis("off")
plt.show()

