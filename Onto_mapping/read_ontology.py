from owlready2 import *

def extract_metadata(entity):
    """
    Extract metadata for a given OWL entity (e.g., comment, label, defined_by).
    """
    metadata = {}
    if hasattr(entity, 'comment'):
        metadata['comment'] = entity.comment
    if hasattr(entity, 'label'):
        metadata['label'] = entity.label
    if hasattr(entity, 'isDefinedBy'):
        metadata['defined_by'] = [str(x) for x in entity.isDefinedBy]
    if hasattr(entity, 'iri'):
        metadata['iri'] = entity.iri
    return metadata

def extract_classes(ontology):
    """
    Extract all classes in the ontology as a list of dictionaries, including subclasses.
    """
    classes = []
    for cls in ontology.classes():
        class_info = {'name': cls.name}
        class_info.update(extract_metadata(cls))
        # Add subclasses
        class_info['subclasses'] = [sub.name for sub in cls.subclasses()]
        classes.append(class_info)
    return classes

def extract_object_properties(ontology):
    """Extract all object properties in the ontology as a list of dictionaries."""
    object_properties = []
    for prop in ontology.object_properties():
        prop_info = {'name': prop.name}
        prop_info.update(extract_metadata(prop))
        object_properties.append(prop_info)
    return object_properties

def extract_data_properties(ontology):
    """Extract all data properties in the ontology as a list of dictionaries."""
    data_properties = []
    for prop in ontology.data_properties():
        prop_info = {'name': prop.name}
        prop_info.update(extract_metadata(prop))
        data_properties.append(prop_info)
    return data_properties

def extract_annotation_properties(ontology):
    """
    Extract all annotation properties in the ontology as a list of dictionaries.
    """
    annotation_properties = []
    for prop in ontology.annotation_properties():
        prop_info = {'name': prop.name}
        prop_info.update(extract_metadata(prop))
        annotation_properties.append(prop_info)
    return annotation_properties

# Load the ontology file
owl_file = "./OWLs/SOMA.owl"  # Replace with the actual file path
onto = get_ontology(owl_file).load()

# Extract entities
classes = extract_classes(onto)
object_properties = extract_object_properties(onto)
data_properties = extract_data_properties(onto)
annotation_properties = extract_annotation_properties(onto)

# Print results
print("Classes:", len(classes))
print("Object Properties:", len(object_properties))
print("Data Properties:", len(data_properties))
print("Annotation Properties:", len(annotation_properties))

print("Class:", classes[0].items())
print("Object Property:", object_properties[2].items())
print("Data Property:", data_properties[2].items())
print("Annotation Property:", annotation_properties[2].items())


