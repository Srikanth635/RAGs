import inspect

from owlready2 import *

# Path to your OWL file
onto_path.append("/home/malineni/PycharmProjects/Llama_index/documentation/External/KGs_OWLs/knowrob.owl")
onto = get_ontology("file:////home/malineni/PycharmProjects/Llama_index/documentation/External/KGs_OWLs/knowrob.owl").load()

from pathlib import Path
from typing import Callable, Dict, List, Optional, Type, Tuple, Union

from owlready2 import (Namespace, Ontology, World as OntologyWorld, Thing, EntityClass, Imp,
                       Property, ObjectProperty, OwlReadyError, types,
                       onto_path, default_world, get_namespace, get_ontology, destroy_entity,
                       sync_reasoner_pellet, sync_reasoner_hermit,
                       OwlReadyOntologyParsingError)
from documentation.External.KGs_OWLs.ontology.ontology_common import  (OntologyConceptHolderStore, OntologyConceptHolder,
                                        ONTOLOGY_SQL_BACKEND_FILE_EXTENSION,
                                        ONTOLOGY_SQL_IN_MEMORY_BACKEND)
from owlready2.class_construct import GeneralClassAxiom
from documentation.External.KGs_OWLs.ontology.ontology import OntologyManager

SOMA_HOME_ONTOLOGY_IRI = "http://www.ease-crc.org/ont/SOMA-HOME.owl"
SOMA_ONTOLOGY_IRI = "http://www.ease-crc.org/ont/SOMA.owl"
KNOWROB_ONTOLOGY_IRI = "https://knowrob.org/kb/knowrob.owl"
SOMA_ONTOLOGY_NAMESPACE = "SOMA"
DUL_ONTOLOGY_NAMESPACE = "DUL"
KNOWROB_ONTOLOGY_NAMESPACE = "KNOWROB"

om = OntologyManager(KNOWROB_ONTOLOGY_IRI)
main_ontology = om.main_ontology
soma = om.soma
dul = om.dul

data_props = list(main_ontology.data_properties())
obj_props = list(main_ontology.object_properties())
classes = list(main_ontology.classes())

print(f"data props {len(data_props)}")
print(f"obj props {len(obj_props)}")
print(f"classes {len(classes)}")

print("base iri ", main_ontology.base_iri)