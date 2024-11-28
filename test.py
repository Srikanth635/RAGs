import plotly.graph_objects as go

# Define the nodes and their detailed descriptions
nodes = {
    "Task": "Pick up the apple and place it on the table",
    "Descriptive Models": (
        "Contribution: Break down the task into steps.\n"
        "Details: Identify actions like detect, grip, move, and place.\n"
        "Example: 'Detect apple' → 'Secure grip' → 'Move to table' → 'Release grip.'"
    ),
    "Predictive Models": (
        "Contribution: Optimize performance.\n"
        "Details: Predict task completion time and minimize errors.\n"
        "Example: Fitts's Law estimates movement time to place the apple."
    ),
    "Cognitive Models": (
        "Contribution: Simulate human thought processes.\n"
        "Details: Ensure actions align with human expectations.\n"
        "Example: Steady movement when placing fragile objects."
    ),
    "Interaction Models": (
        "Contribution: Define communication flows.\n"
        "Details: Provide feedback like 'Apple detected' and 'Task complete.'\n"
        "Example: Notify progress to keep users informed."
    ),
    "UCD Models": (
        "Contribution: Adapt to user needs.\n"
        "Details: Adjust grip strength or placement preferences based on feedback.\n"
        "Example: User specifies to gently place the apple."
    ),
    "System-Oriented Models": (
        "Contribution: Optimize system resources.\n"
        "Details: Coordinate sensors, actuators, and algorithms for precision.\n"
        "Example: Camera detects apple, robotic arm executes grip."
    ),
    "Task and Activity Models": (
        "Contribution: Structure tasks hierarchically.\n"
        "Details: Organize steps like 'Detect apple' → 'Plan path' → 'Place apple.'\n"
        "Example: HTA ensures logical task breakdown."
    ),
    "Social Models": (
        "Contribution: Facilitate collaboration.\n"
        "Details: Assign roles between human and robot or multiple robots.\n"
        "Example: Robot 1 grips, Robot 2 places on the table."
    ),
    "Emotional Models": (
        "Contribution: Adapt to user emotions.\n"
        "Details: Recognize frustration or satisfaction and adjust responses.\n"
        "Example: Reassure user if task takes longer than expected."
    ),
    "Usability Models": (
        "Contribution: Ensure ease of use.\n"
        "Details: Make task execution transparent and intuitive.\n"
        "Example: Provide step-by-step feedback like 'Apple secured, moving to table.'"
    )
}

# Define edges between the task and models
edges = [
    ("Task", "Descriptive Models"),
    ("Task", "Predictive Models"),
    ("Task", "Cognitive Models"),
    ("Task", "Interaction Models"),
    ("Task", "UCD Models"),
    ("Task", "System-Oriented Models"),
    ("Task", "Task and Activity Models"),
    ("Task", "Social Models"),
    ("Task", "Emotional Models"),
    ("Task", "Usability Models")
]

# Create source and target lists for edges
sources = [list(nodes.keys()).index(src) for src, _ in edges]
targets = [list(nodes.keys()).index(trg) for _, trg in edges]

# Create hover text for nodes
hover_text = [f"{key}: {value}" for key, value in nodes.items()]

# Create the interactive graph
fig = go.Figure()

# Add edges
for src, trg in zip(sources, targets):
    fig.add_trace(go.Scatter(
        x=[src, trg],
        y=[10 - src, 10 - trg],  # Positioning for simplicity
        mode="lines",
        line=dict(width=1, color="gray"),
        hoverinfo="none",
        showlegend=False
    ))

# Add nodes
fig.add_trace(go.Scatter(
    x=list(range(len(nodes))),
    y=[10 - i for i in range(len(nodes))],
    mode="markers+text",
    marker=dict(size=20, color="lightblue"),
    text=list(nodes.keys()),
    textposition="top center",
    hoverinfo="text",
    hovertext=hover_text
))

# Configure layout
fig.update_layout(
    title="Interactive Graph: Robot Manipulation Task Execution with Model Contributions",
    title_x=0.5,
    showlegend=False,
    xaxis=dict(visible=False),
    yaxis=dict(visible=False),
    margin=dict(l=50, r=50, t=50, b=50)
)

fig.show()
