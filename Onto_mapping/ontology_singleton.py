from __future__ import annotations
import inspect
import logging
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type, Any
try:
    import owlready2
    from owlready2 import *
except ImportError:
    owlready2 = None
    print("Could not import owlready2, OntologyManager could not be initialized!")

SOMA_HOME_ONTOLOGY_IRI = "http://www.ease-crc.org/ont/SOMA-HOME.owl"
SOMA_ONTOLOGY_IRI = "http://www.ease-crc.org/ont/SOMA.owl"
SOMA_ONTOLOGY_NAMESPACE = "SOMA"
DUL_ONTOLOGY_NAMESPACE = "DUL"

class Singleton(type):
    """
    Metaclass for singletons
    """

    _instances = {}
    """
    Dictionary of singleton child classes inheriting from this metaclass, keyed by child class objects.
    """

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class OntologyManager(object, metaclass=Singleton):

    @classmethod
    def print(cls, ontology_class : str = None):
        """
            Print information (ancestors, super classes, subclasses, properties, etc.) of an ontology class
        """
        if ontology_class is None:
            return
        else:
            ins = cls(main_ontology_iri=SOMA_ONTOLOGY_IRI)
            onto_class = ins.get_ontology_class(ontology_class)
            OntologyManager.print_ontology_class(onto_class)

    def __init__(self, main_ontology_iri: str = "", ontology_search_path: str = f"{Path.home()}/ontologies"):
        Path(ontology_search_path).mkdir(parents=True, exist_ok=True)
        owlready2.onto_path.append(ontology_search_path)

        self.ontologies: Dict[str, owlready2.Ontology] = {}
        self.main_ontology: owlready2.Ontology = None
        self.soma: owlready2.Ontology = None
        self.dul: owlready2.Ontology = None
        self.ontology_world: owlready2.World = None
        self.main_ontology_iri: str = main_ontology_iri
        self.main_ontology_namespace: owlready2.Namespace = None

        self.ontology_world = World(filename=f"{ontology_search_path}/{Path(main_ontology_iri).stem}.sqlite3",
                                    exclusive=False, enable_thread_parallelism=True)
        self.main_ontology, self.main_ontology_namespace = self.load_ontology(main_ontology_iri)
        if self.main_ontology.loaded:
            self.soma = self.ontologies["SOMA"]
            self.dul = self.ontologies["DUL"]

    def load_ontology(self, ontology_iri) -> tuple[owlready2.Ontology, owlready2.Namespace] | None:
        ontology = self.ontology_world.get_ontology(ontology_iri).load(reload_if_newer=True)
        ontology_namespace = owlready2.get_namespace(ontology_iri)
        if ontology.loaded:
            def fetch_ontology(ontology__):
                self.ontologies[ontology__.name] = ontology__

            self.browse_ontologies(ontology, condition=None, func=lambda ontology__: fetch_ontology(ontology__))
            return ontology, ontology_namespace
        return None

    @staticmethod
    def print_ontology_class(ontology_class : owlready2.Thing):
        """
        Print information (ancestors, super classes, subclasses, properties, etc.) of an ontology class
        """
        if ontology_class is None:
            return
        print("-------------------")
        print(f"{ontology_class} {type(ontology_class)}")
        print(f"Super classes: {ontology_class.is_a}")
        print(f"Ancestors: {ontology_class.ancestors()}")
        print(f"Subclasses: {list(ontology_class.subclasses())}")
        print(f"Properties: {list(ontology_class.get_class_properties())}")
        print(f"Instances: {list(ontology_class.instances())}")
        print(f"Direct Instances: {list(ontology_class.direct_instances())}")
        print(f"Inverse Restrictions: {list(ontology_class.inverse_restrictions())}")
        # print(f"Restrictions: {list(cls.get_class_restrictions(ontology_class))}")
        print(f"is-a: {list(ontology_class.is_a)}")

    def initialized(self) -> bool:
        return hasattr(self, "main_ontology") and self.main_ontology.loaded

    @staticmethod
    def browse_ontologies(ontology: owlready2.Ontology, condition=None, func=None, **kwargs) -> None:
        if ontology is None or not ontology.loaded:
            return
        will_do_func = func is not None
        if condition is None:
            if will_do_func:
                func(ontology, **kwargs)
                for sub_onto in ontology.get_imported_ontologies():
                    func(sub_onto, **kwargs)
        elif condition(ontology, **kwargs):
            if will_do_func: func(ontology, **kwargs)
        else:
            for sub_onto in ontology.get_imported_ontologies():
                if condition(sub_onto, **kwargs) and will_do_func:
                    func(sub_onto, **kwargs)
                    break

    # Non-static methods converted to tools below
    def save(self, target_filename: str = "", overwrite: bool = False) -> bool:
        self.ontology_world.save()
        is_current_ontology_local = Path(self.main_ontology_iri).exists()
        current_ontology_filename = self.main_ontology_iri if is_current_ontology_local \
            else f"{Path(self.ontology_world.filename).parent.absolute()}/{Path(self.main_ontology_iri).stem}.owl"
        save_to_same_file = is_current_ontology_local and (target_filename == current_ontology_filename)
        if save_to_same_file and not overwrite:
            return False
        else:
            save_filename = target_filename if target_filename else current_ontology_filename
            self.main_ontology.save(save_filename)
            return True

    # Concept Class Methods
    def create_ontology_concept_class(self, class_name: str, ontology_parent_concept_class=None) -> Type[
        owlready2.Thing]:
        ontology_concept_class = self.get_ontology_class_by_ontology(self.main_ontology, class_name)
        if ontology_concept_class:
            return ontology_concept_class
        with self.main_ontology:
            return types.new_class(class_name, (owlready2.Thing, ontology_parent_concept_class,)
            if inspect.isclass(ontology_parent_concept_class) else (owlready2.Thing,))

    def get_ontology_classes_by_condition(self, condition: Callable, first_match_only=False, **kwargs) \
            -> List[Type[owlready2.Thing]]:
        """
        Get an ontology class by a given condition

        :param condition: condition of searching
        :param first_match_only: whether to only fetch the first class matching the given condition
        :return: The ontology class satisfying the given condition if found else None
        """
        out_classes = []
        for ontology_class in list(self.main_ontology.classes()):
            if condition(ontology_class, **kwargs):
                out_classes.append(ontology_class)
                if first_match_only:
                    return out_classes

        for sub_onto in self.main_ontology.get_imported_ontologies():
            for sub_ontology_class in list(sub_onto.classes()):
                if condition(sub_ontology_class, **kwargs):
                    out_classes.append(sub_ontology_class)
                    if first_match_only:
                        return out_classes

        if not out_classes:
            print(f"No class with {kwargs} is found in the ontology {self.main_ontology}")
        return out_classes

    @staticmethod
    def get_ontology_class_by_ontology(ontology: owlready2.Ontology, class_name: str) -> Type[owlready2.Thing] | None:
        return getattr(ontology, class_name) if ontology and hasattr(ontology, class_name) else None

    def get_ontology_class(self, class_name: str) -> Type[owlready2.Thing] | None:
        """
        Get an ontology class by name

        :param class_name: name of the searched-for ontology class
        :return: The ontology class of the given name if existing else None
        """

        def is_matching_class_name(ontology_class: Type[owlready2.Thing], ontology_class_name: str):
            return ontology_class.name == ontology_class_name

        found_classes = self.get_ontology_classes_by_condition(condition=is_matching_class_name,
                                                               ontology_class_name=class_name,
                                                               first_match_only=True)
        return found_classes[0] if len(found_classes) > 0 else None

    def get_ontology_classes_by_namespace(self, ontology_namespace: str) -> List[Type[owlready2.Thing]]:
        def is_matching_ontology_namespace(ontology_class: Type[owlready2.Thing]):
            return ontology_class.namespace.name == ontology_namespace

        return self.get_ontology_classes_by_condition(condition="is_matching_ontology_namespace")

    def get_ontology_classes_by_subname(self, class_subname: str) -> List[Type[owlready2.Thing]]:
        def is_matching_class_subname(ontology_class: Type[owlready2.Thing]):
            return class_subname.lower() in ontology_class.name.lower()

        return self.get_ontology_classes_by_condition(condition="is_matching_class_subname")

    def get_ontology_descendant_classes(self, ancestor_class_name: str, class_subname: str = "") -> List[
        Type[owlready2.Thing]]:
        ancestor_class = self.get_ontology_class(ancestor_class_name)
        if not ancestor_class:
            return []
        return [ontology_class for ontology_class in self.main_ontology.classes()
                if (class_subname.lower() in ontology_class.name.lower()) and (
                            ancestor_class in ontology_class.ancestors())]

    def create_ontology_triple_classes(self, subject_class_name: str, object_class_name: str, predicate_name: str,
                                       inverse_predicate_name: str, ontology_subject_parent_class=None,
                                       ontology_object_parent_class=None, ontology_property_parent_class=None,
                                       ontology_inverse_property_parent_class=None) -> None:
        with self.main_ontology:
            ontology_subject_class = self.create_ontology_concept_class(subject_class_name,
                                                                        ontology_subject_parent_class)
            ontology_object_class = self.create_ontology_concept_class(object_class_name, ontology_object_parent_class)
            ontology_predicate_class = types.new_class("OntologyPredicate", (owlready2.ObjectProperty,))
            ontology_predicate_class.domain = [ontology_subject_class]
            ontology_predicate_class.range = [ontology_object_class]
            ontology_predicate_class.python_name = predicate_name
            ontology_inverse_predicate = types.new_class("OntologyInversePredicate", (owlready2.ObjectProperty,))
            ontology_inverse_predicate.inverse_property = ontology_predicate_class
            ontology_inverse_predicate.python_name = inverse_predicate_name

    # Instance Individual Methods
    def create_ontology_instance(self, class_name: str, instance_name: str) -> owlready2.Thing:
        """
        Create an instance of an ontology class.

        :param class_name: Name of the ontology class to instantiate.
        :param instance_name: Name to assign to the new instance.
        :return: The created instance.
        """
        ontology_class = self.get_ontology_class(class_name)
        if not ontology_class:
            raise ValueError(f"Class '{class_name}' not found in ontology.")
        if not isinstance(ontology_class, type) or not issubclass(ontology_class, owlready2.Thing):
            raise ValueError(f"'{class_name}' is not a valid Thing class for instantiation.")
        instance_name = instance_name.lower()
        with self.main_ontology:
            # Create the instance explicitly
            instance = ontology_class(name=instance_name)
            if isinstance(instance, owlready2.Thing) and not isinstance(instance, type):
                return instance
            else:
                raise RuntimeError(f"Failed to create instance; '{instance_name}' was interpreted as a class.")

    def get_ontology_instance_by_name(self, class_name: str, instance_name: str) -> owlready2.Thing | None:
        """
        Retrieve an instance of an ontology class by its name.

        :param class_name: Name of the ontology class.
        :param instance_name: Name of the instance to retrieve.
        :return: The instance if found, None otherwise.
        """
        ontology_class = self.get_ontology_class(class_name)
        if not ontology_class:
            raise ValueError(f"Class '{class_name}' not found in ontology.")
        with self.main_ontology:
            for instance in ontology_class.instances():
                if instance.name == instance_name.lower():
                    return instance
        return None

    def get_all_ontology_instances_of_class(self, class_name: str) -> List[owlready2.Thing]:
        """
        Retrieve all instances of an ontology class.

        :param class_name: Name of the ontology class.
        :return: List of all instances of the class.
        """
        ontology_class = self.get_ontology_class(class_name)
        if not ontology_class:
            raise ValueError(f"Class '{class_name}' not found in ontology.")
        with self.main_ontology:
            return list(ontology_class.instances())

    def get_instance_properties(self, class_name: str, instance_name: str) -> Dict[str, Any]:
        """
        Retrieve all properties of an instance.

        :param class_name: Name of the ontology class.
        :param instance_name: Name of the instance.
        :return: Dictionary of property names and their values.
        """
        instance = self.get_ontology_instance_by_name(class_name, instance_name)
        if not instance:
            raise ValueError(f"Instance '{instance_name}' of class '{class_name}' not found.")
        properties = {}
        with self.main_ontology:
            for prop in instance.get_properties():
                prop_values = getattr(instance, prop.python_name, [])
                if isinstance(prop_values, list):
                    properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val in
                                                    prop_values]
                else:
                    properties[prop.python_name] = prop_values.name if hasattr(prop_values, 'name') else str(
                        prop_values)
        return properties

    def get_instance_inverse_properties(self, class_name: str, instance_name: str) -> Dict[str, Any]:
        """
        Retrieve all inverse properties of an instance.

        :param class_name: Name of the ontology class.
        :param instance_name: Name of the instance.
        :return: Dictionary of inverse property names and their values.
        """
        instance = self.get_ontology_instance_by_name(class_name, instance_name)
        if not instance:
            raise ValueError(f"Instance '{instance_name}' of class '{class_name}' not found.")
        inverse_properties = {}
        with self.main_ontology:
            for prop in instance.get_inverse_properties():
                inverse_values = prop[instance]
                if isinstance(inverse_values, list):
                    inverse_properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val in
                                                            inverse_values]
                else:
                    inverse_properties[prop.python_name] = inverse_values.name if hasattr(inverse_values,
                                                                                          'name') else str(
                        inverse_values)
        return inverse_properties

    def get_all_instances_in_ontology(self) -> List[owlready2.Thing]:
        """
        Retrieve all instances across the entire ontology.

        :return: List of all instances in the ontology.
        """
        if not self.main_ontology:
            raise ValueError("Ontology not loaded.")
        all_instances = set()  # Using a set to avoid duplicates from imported ontologies
        with self.main_ontology:
            # Collect instances from the main ontology
            for cls in self.main_ontology.classes():
                all_instances.update(cls.instances())
            # Collect instances from imported ontologies
            for imported_onto in self.main_ontology.get_imported_ontologies():
                for cls in imported_onto.classes():
                    all_instances.update(cls.instances())
        return list(all_instances)

    def get_class_restrictions(self, class_name: str) -> List[str]:
        """
        Retrieve all restrictions (inherited or direct) for a given class.

        :param class_name: Name of the ontology class.
        :return: List of restriction descriptions as strings.
        """
        ontology_class = self.get_ontology_class(class_name)
        if not ontology_class:
            raise ValueError(f"Class '{class_name}' not found in ontology.")

        restrictions = []
        with self.main_ontology:
            # Direct restrictions from is_a
            for restriction in ontology_class.is_a:
                if isinstance(restriction, owlready2.Restriction):
                    restrictions.append(str(restriction))

            # Traverse ancestors to find inherited restrictions
            for ancestor in ontology_class.ancestors():
                if ancestor == ontology_class or ancestor == owlready2.Thing:
                    continue  # Skip the class itself and the top-level Thing
                for restriction in ancestor.is_a:
                    if isinstance(restriction, owlready2.Restriction):
                        restrictions.append(str(restriction))

        return restrictions

    def get_specific_classifies_restriction(self, class_name: str) -> str:
        """
        Retrieve the specific 'classifies only ...' restriction for a given class.

        :param class_name: Name of the ontology class.
        :return: The specific restriction as a string, or an error message.
        """
        restrictions = self.get_class_restrictions(class_name)
        for restriction in restrictions:
            # Look for the specific restriction involving 'classifies'
            if "classifies" in restriction and "hasParticipant" in restriction:
                return restriction
        return f"No 'classifies' restriction found for class '{class_name}'."


if __name__ == "__main__":
    print()

    # om = OntologyManager(SOMA_ONTOLOGY_IRI)
    # print(om.soma.name)
    #
    # cls = om.get_ontology_class("Approaching")
    # om.print_ontology_class(cls)
    # restrictions = om.get_specific_classifies_restriction(class_name=cls.name)
    # print(f"Restrictions: {restrictions}")
    # print(om.get_class_restrictions(class_name=cls.name))



# class OntologyManager(object, metaclass=Singleton):
#     """
#     Singleton class as the adapter accessing data of an OWL ontology, largely based on owlready2.
#
#     Attributes
#     ----------
#     ontologies: Dict[str, owlready2.Ontology]
#         A dictionary of OWL ontologies, keyed by ontology name (same as its namespace name), eg. 'SOMA'
#
#     main_ontology: owlready2.Ontology
#         The main ontology instance as the result of an ontology loading operation
#
#     main_ontology_iri: str
#         Ontology IRI (Internationalized Resource Identifier), either a URL to a remote OWL file or the full name path of a local one
#
#     main_ontology_namespace: owlready2.Namespace
#         Namespace of the main ontology
#
#     soma: owlready2.Ontology
#         The SOMA ontology instance, referencing :attr:`ontology` in case of ontology loading from SOMA.owl
#         Ref: http://www.ease-crc.org/ont/SOMA.owl
#
#     dul: owlready2.Ontology
#         The DUL ontology instance, referencing :attr:`ontology` in case of ontology loading from DUL.owl
#         Ref: http://www.ease-crc.org/ont/DUL.owl
#
#     ontology_world:
#         Ontology world, the placeholder of triples stored by owlready2.
#         Ref: https://owlready2.readthedocs.io/en/latest/world.html
#     """
#
#     def __init__(self, main_ontology_iri: str = "", ontology_search_path: str = f"{Path.home()}/ontologies"):
#         """
#         Create the singleton object of OntologyManager class
#
#         :param main_ontology_iri: Ontology IRI (Internationalized Resource Identifier), either a URL to a remote OWL file
#         or the full name path of a local one
#         :param ontology_search_path: directory path from which a possibly existing ontology is searched. This is appended
#         to `owlready2.onto_path`, a global variable containing a list of directories for searching local copies of
#         ontologies (similarly to python `sys.path` for modules/packages).
#         """
#         if owlready2:
#             Path(ontology_search_path).mkdir(parents=True, exist_ok=True)
#             owlready2.onto_path.append(ontology_search_path)
#         else:
#             return
#
#         self.ontologies: Dict[str, owlready2.Ontology] = {}
#         self.main_ontology: owlready2.Ontology = None
#         self.soma: owlready2.Ontology = None
#         self.dul: owlready2.Ontology = None
#
#         self.ontology_world: owlready2.World = None
#         self.main_ontology_iri: str = main_ontology_iri
#         self.main_ontology_namespace: owlready2.Namespace = None
#
#         # Create an ontology world with parallelized file parsing enabled
#         self.ontology_world = World(filename=f"{ontology_search_path}/{Path(main_ontology_iri).stem}.sqlite3",
#                                     exclusive=False, enable_thread_parallelism=True)
#
#         self.main_ontology, self.main_ontology_namespace = self.load_ontology(main_ontology_iri)
#         if self.main_ontology.loaded:
#             self.soma = self.ontologies[SOMA_ONTOLOGY_NAMESPACE]
#             self.dul = self.ontologies[DUL_ONTOLOGY_NAMESPACE]
#
#     @staticmethod
#     def print_ontology_class(ontology_class):
#         """
#         Print information (ancestors, super classes, subclasses, properties, etc.) of an ontology class
#         """
#         if ontology_class is None:
#             return
#         print("-------------------")
#         print(f"{ontology_class} {type(ontology_class)}")
#         print(f"Super classes: {ontology_class.is_a}")
#         print(f"Ancestors: {ontology_class.ancestors()}")
#         print(f"Subclasses: {list(ontology_class.subclasses())}")
#         print(f"Properties: {list(ontology_class.get_class_properties())}")
#         print(f"Instances: {list(ontology_class.instances())}")
#         print(f"Direct Instances: {list(ontology_class.direct_instances())}")
#         print(f"Inverse Restrictions: {list(ontology_class.inverse_restrictions())}")
#         # print(f"Restrictions: {list(cls.get_class_restrictions(ontology_class))}")
#         print(f"is-a: {list(ontology_class.is_a)}")
#
#
#     def load_ontology(self, ontology_iri) -> tuple[owlready2.Ontology, owlready2.Namespace] | None:
#         """
#         Load an ontology from an IRI
#         :param ontology_iri: An ontology IRI
#         :return: A tuple including an ontology instance & its namespace
#         """
#         ontology = self.ontology_world.get_ontology(ontology_iri).load(reload_if_newer=True)
#         ontology_namespace = owlready2.get_namespace(ontology_iri)
#         if ontology.loaded:
#             print(
#                 f'Ontology [{ontology.base_iri}]\'s name: {ontology.name} has been loaded')
#             print(f'- main namespace: {ontology_namespace.name}')
#             print(f'- loaded ontologies:')
#
#             def fetch_ontology(ontology__):
#                 self.ontologies[ontology__.name] = ontology__
#                 print(ontology__.base_iri)
#
#             self.browse_ontologies(ontology, condition=None, func=lambda ontology__: fetch_ontology(ontology__))
#             return ontology, ontology_namespace
#         else:
#             print(f"Ontology [{ontology.base_iri}]\'s name: {ontology.name} failed being loaded")
#             return None
#
#     def initialized(self) -> bool:
#         return hasattr(self, "main_ontology") and self.main_ontology.loaded
#
#     @staticmethod
#     def browse_ontologies(ontology: owlready2.Ontology,
#                           condition: Optional[Callable] = None, func: Optional[Callable] = None, **kwargs) -> None:
#         """
#         Browse the loaded ontologies (including the main and imported ones), doing operations based on a condition.
#
#         :param ontology: An ontology instance as the result of ontology loading
#         :param condition: a Callable condition that if not None needs to be passed before doing operations, otherwise just
#         always carry the operations
#         :param func: a Callable specifying the operations to perform on all the loaded ontologies if condition is None,
#         otherwise only the first ontology which meets the condition
#         """
#         if ontology is None:
#             print(f"Ontology {ontology=} is None!")
#             return
#         elif not ontology.loaded:
#             print(f"Ontology {ontology} was not loaded!")
#             return
#
#         will_do_func = func is not None
#         # No condition: Do func for all ontologies
#         if condition is None:
#             if will_do_func:
#                 func(ontology, **kwargs)
#                 for sub_onto in ontology.get_imported_ontologies():
#                     func(sub_onto, **kwargs)
#         # Else: Only do func for the first ontology which meets the condition
#         elif condition(ontology, **kwargs):
#             if will_do_func: func(ontology, **kwargs)
#         else:
#             for sub_onto in ontology.get_imported_ontologies():
#                 if condition(sub_onto, **kwargs) and will_do_func:
#                     func(sub_onto, **kwargs)
#                     break
#
#     def save(self, target_filename: str = "", overwrite: bool = False) -> bool:
#         """
#         Save the current ontology to disk
#         :param target_filename: full name path of a file which the ontologies are saved into.
#         :param overwrite: overwrite an existing file if it exists.
#         If empty, they are saved to the same original OWL file from which the main ontology was loaded, or
#         a file at the same folder with ontology search path specified at constructor if it was loaded from a remote IRI.
#         :return: True if the ontology was successfully saved, False otherwise
#         """
#
#         # Commit the whole graph data of the current ontology world, saving it into SQLite3, to be reused the next time
#         # the ontologies are loaded
#         self.ontology_world.save()
#
#         # Save ontologies to OWL
#         is_current_ontology_local = Path(self.main_ontology_iri).exists()
#         current_ontology_filename = self.main_ontology_iri if is_current_ontology_local \
#             else f"{Path(self.ontology_world.filename).parent.absolute()}/{Path(self.main_ontology_iri).stem}.owl"
#         save_to_same_file = is_current_ontology_local and (target_filename == current_ontology_filename)
#         if save_to_same_file and not overwrite:
#             print(f"Ontologies cannot be saved to the originally loaded [{target_filename}] if not by overwriting")
#             return False
#         else:
#             save_filename = target_filename if target_filename else current_ontology_filename
#             self.main_ontology.save(save_filename)
#             if save_to_same_file and overwrite:
#                 print(f"Ontologies have been overwritten to {save_filename}")
#             else:
#                 print(f"Ontologies have been saved to {save_filename}")
#             return True
#
#     def create_ontology_concept_class(self, class_name: str,
#                                       ontology_parent_concept_class: Optional[owlready2.Thing] = None) \
#             -> Type[owlready2.Thing]:
#         """
#         Create a new concept class in ontology
#
#         :param class_name: A given name to the new class
#         :param ontology_parent_concept_class: An optional parent ontology class of the new class
#         :return: The created ontology class
#         """
#         ontology_concept_class = self.get_ontology_class_by_ontology(self.main_ontology, class_name)
#         if ontology_concept_class:
#             return ontology_concept_class
#
#         with self.main_ontology:
#             return types.new_class(class_name, (owlready2.Thing, ontology_parent_concept_class,)
#                    if inspect.isclass(ontology_parent_concept_class) else (owlready2.Thing,))
#
#     @staticmethod
#     def create_ontology_property_class(class_name: str,
#                                        ontology_parent_property_class: Optional[Type[owlready2.Property]] = None) \
#             -> Type[owlready2.Property] | None:
#         """
#         Create a new property class in ontology
#
#         :param class_name: A given name to the new class
#         :param ontology_parent_property_class: An optional parent ontology property class of the new class
#         :return: The created ontology class
#         """
#         parent_class = ontology_parent_property_class if (ontology_parent_property_class and
#                                                           issubclass(ontology_parent_property_class,
#                                                                      owlready2.Property)) \
#             else None
#         return types.new_class(class_name, (parent_class,) if parent_class else (owlready2.Property,))
#
#     def get_ontology_classes_by_condition(self, condition: Callable, first_match_only=False, **kwargs) \
#             -> List[Type[owlready2.Thing]]:
#         """
#         Get an ontology class by a given condition
#
#         :param condition: condition of searching
#         :param first_match_only: whether to only fetch the first class matching the given condition
#         :return: The ontology class satisfying the given condition if found else None
#         """
#         out_classes = []
#         for ontology_class in list(self.main_ontology.classes()):
#             if condition(ontology_class, **kwargs):
#                 out_classes.append(ontology_class)
#                 if first_match_only:
#                     return out_classes
#
#         for sub_onto in self.main_ontology.get_imported_ontologies():
#             for sub_ontology_class in list(sub_onto.classes()):
#                 if condition(sub_ontology_class, **kwargs):
#                     out_classes.append(sub_ontology_class)
#                     if first_match_only:
#                         return out_classes
#
#         if not out_classes:
#             print(f"No class with {kwargs} is found in the ontology {self.main_ontology}")
#         return out_classes
#
#     @staticmethod
#     def get_ontology_class_by_ontology(ontology: owlready2.Ontology, class_name: str) -> Type[owlready2.Thing] | None:
#         """
#         Get an ontology class if it exists in a given ontology
#
#         :param ontology: an ontology instance
#         :return: The ontology class if it exists under the namespace of the given ontology, None otherwise
#         """
#         return getattr(ontology, class_name) if ontology and hasattr(ontology, class_name) else None
#
#     def get_ontology_class(self, class_name: str) -> Type[owlready2.Thing] | None:
#         """
#         Get an ontology class by name
#
#         :param class_name: name of the searched-for ontology class
#         :return: The ontology class of the given name if existing else None
#         """
#
#         def is_matching_class_name(ontology_class: Type[owlready2.Thing], ontology_class_name: str):
#             return ontology_class.name == ontology_class_name
#
#         found_classes = self.get_ontology_classes_by_condition(condition=is_matching_class_name,
#                                                                ontology_class_name=class_name,
#                                                                first_match_only=True)
#         return found_classes[0] if len(found_classes) > 0 else None
#
#     def get_ontology_classes_by_namespace(self, ontology_namespace: str) -> List[
#         Type[owlready2.Thing]]:
#         """
#         Get all ontologies classes by namespace
#
#         :param ontology_namespace: namespace of the searched-for ontology classes
#         :return: A list of the ontology classes under the given namespace
#         """
#
#         def is_matching_ontology_namespace(ontology_class: Type[owlready2.Thing], ontology_namespace_: str):
#             return ontology_class.namespace.name == ontology_namespace_
#
#         return self.get_ontology_classes_by_condition(condition=is_matching_ontology_namespace,
#                                                       ontology_namespace_=ontology_namespace)
#
#     def get_ontology_classes_by_subname(self, class_subname: str) -> List[Type[owlready2.Thing]]:
#         """
#         Get all ontologies classes by subname
#
#         :param class_subname: a string as part of the full names of the searched-for ontology classes
#         :return: A list of the ontology classes of which the name contains the given subname
#         """
#
#         def is_matching_class_subname(ontology_class: Type[owlready2.Thing], ontology_class_subname: str):
#             return ontology_class_subname.lower() in ontology_class.name.lower()
#
#         return self.get_ontology_classes_by_condition(condition=is_matching_class_subname,
#                                                       ontology_class_subname=class_subname)
#
#     def get_ontology_descendant_classes(self, ancestor_class: Type[owlready2.Thing], class_subname: str = "") \
#             -> List[Type[owlready2.Thing]]:
#         """
#         Get ontology descendant classes of an ancestor class given descendant class subname
#
#         :param class_subname: a string as part of the ancestor class full name
#         :return: A list of the ontology descendant classes
#         """
#         return [ontology_class for ontology_class in self.main_ontology.classes()
#                 if (class_subname.lower() in ontology_class.name.lower()) and
#                 (ancestor_class in ontology_class.ancestors())]
#
#     def create_ontology_triple_classes(self, subject_class_name: str, object_class_name: str,
#                                        predicate_name: str, inverse_predicate_name: str,
#                                        ontology_subject_parent_class: Optional[Type[owlready2.Thing]] = None,
#                                        ontology_object_parent_class: Optional[Type[owlready2.Thing]] = None,
#                                        ontology_property_parent_class: Optional[Type[
#                                            owlready2.Property]] = owlready2.ObjectProperty if owlready2 else None,
#                                        ontology_inverse_property_parent_class: Optional[Type[
#                                            owlready2.Property]] = owlready2.ObjectProperty if owlready2 else None) -> None:
#         """
#         Dynamically create ontology triple classes under same namespace with the main ontology,
#         as known as {subject, predicate, object}, with the relations among them
#
#         :param subject_class_name: name of the subject class
#         :param object_class_name: name of the object class
#         :param predicate_name: name of predicate class, also used as a Python attribute of the subject class to
#         query object instances
#         :param inverse_predicate_name: name of inverse predicate
#         :param ontology_subject_parent_class: a parent class of the subject class
#         :param ontology_object_parent_class: a parent class of the object class
#         :param ontology_property_parent_class: a parent ontology property class, default: owlready2.ObjectProperty
#         :param ontology_inverse_property_parent_class: a parent ontology inverse property class, default: owlready2.ObjectProperty
#         """
#
#         # This context manager ensures all classes created here-in share the same namepsace with `self.main_ontology`
#         with self.main_ontology:
#             # Subject
#             ontology_subject_class = self.create_ontology_concept_class(subject_class_name,
#                                                                         ontology_subject_parent_class)
#
#             # Object
#             ontology_object_class = self.create_ontology_concept_class(object_class_name, ontology_object_parent_class)
#
#             # Predicate
#             ontology_predicate_class = self.create_ontology_property_class("OntologyPredicate",
#                                                                            ontology_property_parent_class)
#             ontology_predicate_class.domain = [ontology_subject_class]
#             ontology_predicate_class.range = [ontology_object_class]
#             ontology_predicate_class.python_name = predicate_name
#
#             # Inverse Predicate
#             ontology_inverse_predicate = self.create_ontology_property_class("OntologyInversePredicate",
#                                                                              ontology_inverse_property_parent_class)
#             ontology_inverse_predicate.inverse_property = ontology_predicate_class
#             ontology_inverse_predicate.python_name = inverse_predicate_name
#
#         # Instance Individual Methods
#         def create_ontology_instance(self, class_name: str, instance_name: str) -> owlready2.Thing:
#             """
#             Create an instance of an ontology class.
#
#             :param class_name: Name of the ontology class to instantiate.
#             :param instance_name: Name to assign to the new instance.
#             :return: The created instance.
#             """
#             ontology_class = self.get_ontology_class(class_name)
#             if not ontology_class:
#                 raise ValueError(f"Class '{class_name}' not found in ontology.")
#             if not isinstance(ontology_class, type) or not issubclass(ontology_class, owlready2.Thing):
#                 raise ValueError(f"'{class_name}' is not a valid Thing class for instantiation.")
#             instance_name = instance_name.lower()
#             with self.main_ontology:
#                 # Create the instance explicitly
#                 instance = ontology_class(name=instance_name)
#                 if isinstance(instance, owlready2.Thing) and not isinstance(instance, type):
#                     return instance
#                 else:
#                     raise RuntimeError(f"Failed to create instance; '{instance_name}' was interpreted as a class.")
#
#         def get_ontology_instance_by_name(self, class_name: str, instance_name: str) -> owlready2.Thing | None:
#             """
#             Retrieve an instance of an ontology class by its name.
#
#             :param class_name: Name of the ontology class.
#             :param instance_name: Name of the instance to retrieve.
#             :return: The instance if found, None otherwise.
#             """
#             ontology_class = self.get_ontology_class(class_name)
#             if not ontology_class:
#                 raise ValueError(f"Class '{class_name}' not found in ontology.")
#             with self.main_ontology:
#                 for instance in ontology_class.instances():
#                     if instance.name == instance_name.lower():
#                         return instance
#             return None
#
#         def get_all_ontology_instances_of_class(self, class_name: str) -> List[owlready2.Thing]:
#             """
#             Retrieve all instances of an ontology class.
#
#             :param class_name: Name of the ontology class.
#             :return: List of all instances of the class.
#             """
#             ontology_class = self.get_ontology_class(class_name)
#             if not ontology_class:
#                 raise ValueError(f"Class '{class_name}' not found in ontology.")
#             with self.main_ontology:
#                 return list(ontology_class.instances())
#
#         def get_instance_properties(self, class_name: str, instance_name: str) -> Dict[str, Any]:
#             """
#             Retrieve all properties of an instance.
#
#             :param class_name: Name of the ontology class.
#             :param instance_name: Name of the instance.
#             :return: Dictionary of property names and their values.
#             """
#             instance = self.get_ontology_instance_by_name(class_name, instance_name)
#             if not instance:
#                 raise ValueError(f"Instance '{instance_name}' of class '{class_name}' not found.")
#             properties = {}
#             with self.main_ontology:
#                 for prop in instance.get_properties():
#                     prop_values = getattr(instance, prop.python_name, [])
#                     if isinstance(prop_values, list):
#                         properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val in
#                                                         prop_values]
#                     else:
#                         properties[prop.python_name] = prop_values.name if hasattr(prop_values, 'name') else str(
#                             prop_values)
#             return properties
#
#         def get_instance_inverse_properties(self, class_name: str, instance_name: str) -> Dict[str, Any]:
#             """
#             Retrieve all inverse properties of an instance.
#
#             :param class_name: Name of the ontology class.
#             :param instance_name: Name of the instance.
#             :return: Dictionary of inverse property names and their values.
#             """
#             instance = self.get_ontology_instance_by_name(class_name, instance_name)
#             if not instance:
#                 raise ValueError(f"Instance '{instance_name}' of class '{class_name}' not found.")
#             inverse_properties = {}
#             with self.main_ontology:
#                 for prop in instance.get_inverse_properties():
#                     inverse_values = prop[instance]
#                     if isinstance(inverse_values, list):
#                         inverse_properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val
#                                                                 in
#                                                                 inverse_values]
#                     else:
#                         inverse_properties[prop.python_name] = inverse_values.name if hasattr(inverse_values,
#                                                                                               'name') else str(
#                             inverse_values)
#             return inverse_properties
#
#         def get_all_instances_in_ontology(self) -> List[owlready2.Thing]:
#             """
#             Retrieve all instances across the entire ontology.
#
#             :return: List of all instances in the ontology.
#             """
#             if not self.main_ontology:
#                 raise ValueError("Ontology not loaded.")
#             all_instances = set()  # Using a set to avoid duplicates from imported ontologies
#             with self.main_ontology:
#                 # Collect instances from the main ontology
#                 for cls in self.main_ontology.classes():
#                     all_instances.update(cls.instances())
#                 # Collect instances from imported ontologies
#                 for imported_onto in self.main_ontology.get_imported_ontologies():
#                     for cls in imported_onto.classes():
#                         all_instances.update(cls.instances())
#             return list(all_instances)
#
#     # Instance Individual Methods
#     def create_ontology_instance(self, class_name: str, instance_name: str) -> owlready2.Thing:
#         """
#         Create an instance of an ontology class.
#
#         :param class_name: Name of the ontology class to instantiate.
#         :param instance_name: Name to assign to the new instance.
#         :return: The created instance.
#         """
#         ontology_class = self.get_ontology_class(class_name)
#         if not ontology_class:
#             raise ValueError(f"Class '{class_name}' not found in ontology.")
#         if not isinstance(ontology_class, type) or not issubclass(ontology_class, owlready2.Thing):
#             raise ValueError(f"'{class_name}' is not a valid Thing class for instantiation.")
#         instance_name = instance_name.lower()
#         with self.main_ontology:
#             # Create the instance explicitly
#             instance = ontology_class(name=instance_name)
#             if isinstance(instance, owlready2.Thing) and not isinstance(instance, type):
#                 return instance
#             else:
#                 raise RuntimeError(f"Failed to create instance; '{instance_name}' was interpreted as a class.")
#
#     def get_ontology_instance_by_name(self, class_name: str, instance_name: str) -> owlready2.Thing | None:
#         """
#         Retrieve an instance of an ontology class by its name.
#
#         :param class_name: Name of the ontology class.
#         :param instance_name: Name of the instance to retrieve.
#         :return: The instance if found, None otherwise.
#         """
#         ontology_class = self.get_ontology_class(class_name)
#         if not ontology_class:
#             raise ValueError(f"Class '{class_name}' not found in ontology.")
#         with self.main_ontology:
#             for instance in ontology_class.instances():
#                 if instance.name == instance_name.lower():
#                     return instance
#         return None
#
#     def get_all_ontology_instances_of_class(self, class_name: str) -> List[owlready2.Thing]:
#         """
#         Retrieve all instances of an ontology class.
#
#         :param class_name: Name of the ontology class.
#         :return: List of all instances of the class.
#         """
#         ontology_class = self.get_ontology_class(class_name)
#         if not ontology_class:
#             raise ValueError(f"Class '{class_name}' not found in ontology.")
#         with self.main_ontology:
#             return list(ontology_class.instances())
#
#     def get_instance_properties(self, class_name: str, instance_name: str) -> Dict[str, Any]:
#         """
#         Retrieve all properties of an instance.
#
#         :param class_name: Name of the ontology class.
#         :param instance_name: Name of the instance.
#         :return: Dictionary of property names and their values.
#         """
#         instance = self.get_ontology_instance_by_name(class_name, instance_name)
#         if not instance:
#             raise ValueError(f"Instance '{instance_name}' of class '{class_name}' not found.")
#         properties = {}
#         with self.main_ontology:
#             for prop in instance.get_properties():
#                 prop_values = getattr(instance, prop.python_name, [])
#                 if isinstance(prop_values, list):
#                     properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val in
#                                                     prop_values]
#                 else:
#                     properties[prop.python_name] = prop_values.name if hasattr(prop_values, 'name') else str(
#                         prop_values)
#         return properties
#
#     def get_instance_inverse_properties(self, class_name: str, instance_name: str) -> Dict[str, Any]:
#         """
#         Retrieve all inverse properties of an instance.
#
#         :param class_name: Name of the ontology class.
#         :param instance_name: Name of the instance.
#         :return: Dictionary of inverse property names and their values.
#         """
#         instance = self.get_ontology_instance_by_name(class_name, instance_name)
#         if not instance:
#             raise ValueError(f"Instance '{instance_name}' of class '{class_name}' not found.")
#         inverse_properties = {}
#         with self.main_ontology:
#             for prop in instance.get_inverse_properties():
#                 inverse_values = prop[instance]
#                 if isinstance(inverse_values, list):
#                     inverse_properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val
#                                                             in
#                                                             inverse_values]
#                 else:
#                     inverse_properties[prop.python_name] = inverse_values.name if hasattr(inverse_values,
#                                                                                           'name') else str(
#                         inverse_values)
#         return inverse_properties
#
#     def get_all_instances_in_ontology(self) -> List[owlready2.Thing]:
#         """
#         Retrieve all instances across the entire ontology.
#
#         :return: List of all instances in the ontology.
#         """
#         if not self.main_ontology:
#             raise ValueError("Ontology not loaded.")
#         all_instances = set()  # Using a set to avoid duplicates from imported ontologies
#         with self.main_ontology:
#             # Collect instances from the main ontology
#             for cls in self.main_ontology.classes():
#                 all_instances.update(cls.instances())
#             # Collect instances from imported ontologies
#             for imported_onto in self.main_ontology.get_imported_ontologies():
#                 for cls in imported_onto.classes():
#                     all_instances.update(cls.instances())
#         return list(all_instances)
#
#     def get_class_restrictions(self, class_name: str) -> List[str]:
#         """
#         Retrieve all restrictions (inherited or direct) for a given class.
#
#         :param class_name: Name of the ontology class.
#         :return: List of restriction descriptions as strings.
#         """
#         ontology_class = self.get_ontology_class(class_name)
#         if not ontology_class:
#             raise ValueError(f"Class '{class_name}' not found in ontology.")
#
#         restrictions = []
#         with self.main_ontology:
#             # Direct restrictions from is_a
#             for restriction in ontology_class.is_a:
#                 if isinstance(restriction, owlready2.Restriction):
#                     restrictions.append(str(restriction))
#
#             # Traverse ancestors to find inherited restrictions
#             for ancestor in ontology_class.ancestors():
#                 if ancestor == ontology_class or ancestor == owlready2.Thing:
#                     continue  # Skip the class itself and the top-level Thing
#                 for restriction in ancestor.is_a:
#                     if isinstance(restriction, owlready2.Restriction):
#                         restrictions.append(str(restriction))
#
#         return restrictions
#
#     def get_specific_classifies_restriction(self, class_name: str) -> str:
#         """
#         Retrieve the specific 'classifies only ...' restriction for a given class.
#
#         :param class_name: Name of the ontology class.
#         :return: The specific restriction as a string, or an error message.
#         """
#         restrictions = self.get_class_restrictions(class_name)
#         for restriction in restrictions:
#             # Look for the specific restriction involving 'classifies'
#             if "classifies" in restriction and "hasParticipant" in restriction:
#                 return restriction
#         return f"No 'classifies' restriction found for class '{class_name}'."