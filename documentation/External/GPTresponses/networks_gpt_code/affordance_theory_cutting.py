from graphviz import Digraph

# Create a directed graph for cutting an apple using affordance theory
dot = Digraph("Cutting_Apple_Affordance", format="png")

# Define main steps
dot.node("1", "1. Perception")
dot.node("2", "2. Contextual Understanding")
dot.node("3", "3. Action Mapping")
dot.node("4", "4. Task Planning")
dot.node("5", "5. Execution")
dot.node("6", "6. Monitoring and Feedback")
dot.node("7", "7. Post-Action Assessment")

# Add sub-steps for Perception
dot.node("1.1", "Object Identification: Detect apple and knife")
dot.node("1.2", "Affordance Recognition: Apple affords slicing")
dot.edge("1", "1.1")
dot.edge("1", "1.2")

# Add sub-steps for Contextual Understanding
dot.node("2.1", "Action Context Analysis: Define goal (e.g., halving or slicing)")
dot.node("2.2", "Environmental Constraints Analysis: Stability of cutting board")
dot.edge("2", "2.1")
dot.edge("2", "2.2")

# Add sub-steps for Action Mapping
dot.node("3.1", "Tool Affordances: Knife affords slicing")
dot.node("3.2", "Object Affordances: Apple’s texture and stability")
dot.node("3.3", "Compatibility Check: Ensure knife is suitable for cutting apple")
dot.edge("3", "3.1")
dot.edge("3", "3.2")
dot.edge("3", "3.3")

# Add sub-steps for Task Planning
dot.node("4.1", "Action Segmentation: Pick knife, stabilize apple, cut")
dot.node("4.2", "Motion Planning: Plan trajectory of cut")
dot.node("4.3", "Force and Stability Analysis: Calculate required force")
dot.edge("4", "4.1")
dot.edge("4", "4.2")
dot.edge("4", "4.3")

# Add sub-steps for Execution
dot.node("5.1", "Tool Engagement: Grip knife securely")
dot.node("5.2", "Precise Positioning: Align knife with apple")
dot.node("5.3", "Cutting Action: Apply force along trajectory")
dot.edge("5", "5.1")
dot.edge("5", "5.2")
dot.edge("5", "5.3")

# Add sub-steps for Monitoring and Feedback
dot.node("6.1", "Sensory Feedback: Monitor force and position")
dot.node("6.2", "Error Detection: Correct if apple shifts or cut is uneven")
dot.edge("6", "6.1")
dot.edge("6", "6.2")

# Add sub-steps for Post-Action Assessment
dot.node("7.1", "Outcome Verification: Inspect slices for completeness")
dot.node("7.2", "Learning: Record parameters for improvement")
dot.edge("7", "7.1")
dot.edge("7", "7.2")

# Connect main steps sequentially
dot.edge("1", "2")
dot.edge("2", "3")
dot.edge("3", "4")
dot.edge("4", "5")
dot.edge("5", "6")
dot.edge("6", "7")

# Render the flowchart
dot.render("/mnt/new_logs/Cutting_Apple_Affordance")

# Provide the file location to the user
"/mnt/new_logs/Cutting_Apple_Affordance.png"
