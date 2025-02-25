from owlready2 import *
from openai import OpenAI
import dotenv
dotenv.load_dotenv()
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)
import ollama

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
    """Extract all new_logs properties in the ontology as a list of dictionaries."""
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
# print("Classes:", len(classes))
# print("Object Properties:", len(object_properties))
# print("Data Properties:", len(data_properties))
# print("Annotation Properties:", len(annotation_properties))
#
# print("Class:", classes[0].items())
# print("Object Property:", object_properties[2].items())
# print("Data Property:", data_properties[2].items())
# print("Annotation Property:", annotation_properties[2].items())

def gpt_call(concept_names, attributes):
    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are an expert mapper from attributes to SOMA concepts. Your task is to map each provided "
                           "attribute to semantically most relevant and specific SOMA concept name strictly. stick the"
                           "concept names provided strictly, dont create new concept names by yourself"
            },
            {
                "role": "assistant",
                "content": f"Available SOMA concept names : \n\n  {concept_names}"
            },
            {
                "role": "user",
                "content": f"Attributes to be mapped are \n\n {attributes} \n\n "
                           f"Output: Give out the updated mapped list of attributes"
            },
        ]
    )
    return resp

def get_semantic_match(attribute, classes):
    """
    Use the OpenAI ChatGPT API to find the most semantically similar class for the attribute.
    """
    # Prepare the prompt
    prompt = f"""
    You are an ontology matching assistant. Your task is to find the most semantically similar class for the attribute: "{attribute}".

    Here is a list of ontology classes with their names and descriptions:
    {classes}

    Return the name of the most semantically similar class for the attribute "{attribute}". If no suitable match is found, return "None".
    """

    # Call the OpenAI API
    response = ollama.chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": "You are an ontology matching assistant."},
            {"role": "user", "content": prompt}
        ],
        # max_tokens=100,
        # temperature=0.2  # Lower temperature for more deterministic responses
    )
    print(f"Ollama Called and the response is {response}")
    # Extract the matched class from the response
    matched_class = response["message"]["content"].strip()
    return matched_class

def map_attributes_to_ontology(cram_action, ontology_file, threshold=0.7):
    """
    Map the attributes of the CRAM action designator to the ontology concepts using an LLM.
    Returns a dictionary where each attribute is mapped to:
    - The closest match (most semantically similar class).
    - A list of all matches that exceed the similarity threshold.
    """
    # Load the ontology
    # graph = load_ontology(ontology_file)
    onto = get_ontology(ontology_file).load()

    # Extract all entities (classes/concepts) and their hierarchy
    # concepts = extract_concepts(graph)
    concepts = extract_classes(onto)
    # classes = extract_classes()

    # Iterate over the CRAM action designator attributes
    mapped_action = {}
    for attr, value in cram_action.items():
        # Prepare the list of classes for the LLM
        classes_for_llm = "\n".join(
            [
                f"- Name: {concept['name']}, Description: {concept['comment'][0] if concept['comment'] else 'No description'}"
                for concept in concepts]
        )

        # Get the most semantically similar class using the LLM
        matched_class = get_semantic_match(attr, classes_for_llm)

        if matched_class and matched_class.lower() != "none":
            # Find the matched concept dictionary
            matched_concept = next((concept for concept in concepts if concept["name"] == matched_class), None)
            if matched_concept:
                mapped_action[attr] = {
                    "closest_match": matched_concept["name"],
                    "value": value
                }
            else:
                mapped_action[attr] = {
                    "closest_match": None,
                    "value": value
                }
        else:
            mapped_action[attr] = {
                "closest_match": None,
                "value": value
            }

    return mapped_action
    # return concepts, classes_for_llm

if __name__ == "__main__":
    cram_action = {
        "cutting": "cup",
        "length": 15,
        "sharpness": "high",
        "initial-force": 2.0
    }
    ontology_file = "OWLs/SOMA.owl"

    mapped_action = map_attributes_to_ontology(cram_action, ontology_file)

    print("Original CRAM Action:", cram_action)
    print("Mapped CRAM Action with LLM Semantic Matching:")
    for attr, details in mapped_action.items():
        print(f"Attribute: {attr}")
        print(f"  Closest Match: {details['closest_match']}")
        print(f"  Value: {details['value']}")
        print()
    # i = 2
    # concepts = extract_classes(onto)
    # print(len(concepts), concepts[i].keys())
    # # print(concepts[i]['name'])
    # # print(concepts[i]['comment'])
    # # print(concepts[i]['label'])
    # # print(concepts[i]['defined_by'])
    # # print(concepts[i]['iri'])
    # # print(concepts[i]['subclasses'])
    #
    # concept_names = [concept["name"] for concept in concepts]
    # attributes = ['shape','size','colour']
    #
    # response = gpt_call(concept_names, attributes)
    # print(response.choices[0].message.content)





