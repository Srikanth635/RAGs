from owlready2 import *

onto = get_ontology("file:////home/malineni/PycharmProjects/Llama_index/documentation/External/KGs_OWLs/knowrob.owl").load()

print(list(onto.classes()))