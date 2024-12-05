from graphviz import Digraph

# Create a new directed graph
dot = Digraph()

# Define nodes for the flowchart
dot.node('A', 'Start')
dot.node('B', 'Identify Box')
dot.node('C', 'Check Box Orientation')
dot.node('D', 'Approach Box')
dot.node('E', 'Pick Up Box')
dot.node('F', 'Transport to Shelf')
dot.node('G', 'Identify Shelf Location')
dot.node('H', 'Place Box on Shelf')
dot.node('I', 'Update User on Progress')
dot.node('J', 'End')

# Define edges to connect the nodes
dot.edges(['AB', 'BC', 'CD', 'DE', 'EF', 'FG', 'GH', 'HI', 'IJ'])

# Render the flowchart to a file and display it
dot.render('flowchart', format='png', cleanup=True)
dot.view()