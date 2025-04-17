from __future__ import annotations
import json
import inspect
from typing import Annotated, List, Dict, Any, Optional, Type, Callable
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.tool import tool_call, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_core.tools import Tool, tool
from langgraph.prebuilt import ToolNode, tools_condition
from dotenv import load_dotenv, find_dotenv
import owlready2
from owlready2 import *
from pathlib import Path
import types
load_dotenv(find_dotenv(), override=True)

from ontology_singleton import *
ONTOLOGY_FILE = "http://www.ease-crc.org/ont/SOMA.owl"
om = OntologyManager(ONTOLOGY_FILE)

# 1. Configuration
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.3

# 2. State Definition
class State(TypedDict):
    messages: Annotated[list, add_messages]

# 3. Tools (Non-static methods from OntologyManager)
@tool
def save(target_filename: str = "", overwrite: bool = False) -> bool:
    """Save the current ontology to disk."""
    return om.save(target_filename, overwrite)

@tool
def create_ontology_concept_class(class_name: str, ontology_parent_concept_class: Optional[str] = None) -> str:
    """Create a new concept class in the ontology."""
    parent_class = om.get_ontology_class(ontology_parent_concept_class) if ontology_parent_concept_class else None
    result = om.create_ontology_concept_class(class_name, parent_class)
    return result.name if result else "None"

@tool
def get_ontology_classes_by_condition(condition: str, first_match_only: bool = False) -> List[str]:
    """Get ontology classes by a condition."""
    result = om.get_ontology_classes_by_condition(condition, first_match_only)
    return [cls.name for cls in result]

@tool
def get_ontology_class(class_name: str) -> str:
    """Get an ontology class by name."""
    result = om.get_ontology_class(class_name)
    return result.name if result else "None"

@tool
def get_ontology_classes_by_namespace(ontology_namespace: str) -> List[str]:
    """Get all ontology classes by namespace."""
    result = om.get_ontology_classes_by_namespace(ontology_namespace)
    return [cls.name for cls in result]

@tool
def get_ontology_classes_by_subname(class_subname: str) -> List[str]:
    """Get all ontology classes which contains the given class_subname substring in them."""
    result = om.get_ontology_classes_by_subname(class_subname)
    return [cls.name for cls in result]

@tool
def get_ontology_descendant_classes(ancestor_class_name: str, class_subname: str = "") -> List[str]:
    """Get ontology descendant classes of an ancestor class."""
    result = om.get_ontology_descendant_classes(ancestor_class_name, class_subname)
    return [cls.name for cls in result]

@tool
def create_ontology_triple_classes(subject_class_name: str, object_class_name: str, predicate_name: str,
                                   inverse_predicate_name: str, ontology_subject_parent_class: Optional[str] = None,
                                   ontology_object_parent_class: Optional[str] = None) -> str:
    """Create ontology triple classes."""
    subj_parent = om.get_ontology_class(ontology_subject_parent_class) if ontology_subject_parent_class else None
    obj_parent = om.get_ontology_class(ontology_object_parent_class) if ontology_object_parent_class else None
    om.create_ontology_triple_classes(subject_class_name, object_class_name, predicate_name, inverse_predicate_name,
                                      subj_parent, obj_parent)
    return f"Triple created: {subject_class_name} -> {predicate_name} -> {object_class_name}"

@tool
def create_ontology_instance(class_name: str, instance_name: str) -> str:
    """
    Create an instance of an ontology class.

    :param class_name: Name of the ontology class to instantiate.
    :param instance_name: Name to assign to the new instance.
    :return: The name of the created instance or an error message.
    """
    try:
        result = om.create_ontology_instance(class_name, instance_name)
        return result.name if result else "Instance creation failed"
    except ValueError as e:
        return str(e)
    except TypeError as e:
        return f"TypeError: Unable to create instance of '{class_name}' - {str(e)}"

@tool
def get_ontology_instance_by_name(class_name: str, instance_name: str) -> str:
    """
    Retrieve an instance of an ontology class by its name.

    :param class_name: Name of the ontology class.
    :param instance_name: Name of the instance to retrieve.
    :return: The name of the instance if found, or an error message.
    """
    try:
        result = om.get_ontology_instance_by_name(class_name, instance_name)
        return result.name if result else f"Instance '{instance_name}' not found in class '{class_name}'"
    except ValueError as e:
        return str(e)

@tool
def get_all_ontology_instances_of_class(class_name: str) -> str:
    """
    Retrieve all instances of an ontology class.

    :param class_name: Name of the ontology class.
    :return: List of instance names as a JSON string, or an error message.
    """
    try:
        result = om.get_all_ontology_instances_of_class(class_name)
        instance_names = [inst.name for inst in result]
        return json.dumps(instance_names)
    except ValueError as e:
        return str(e)

@tool
def get_instance_properties(class_name: str, instance_name: str) -> str:
    """
    Retrieve all properties of an instance.

    :param class_name: Name of the ontology class.
    :param instance_name: Name of the instance.
    :return: Dictionary of properties as a JSON string, or an error message.
    """
    try:
        result = om.get_instance_properties(class_name, instance_name)
        return json.dumps(result)
    except ValueError as e:
        return str(e)

@tool
def get_instance_inverse_properties(class_name: str, instance_name: str) -> str:
    """
    Retrieve all inverse properties of an instance.

    :param class_name: Name of the ontology class.
    :param instance_name: Name of the instance.
    :return: Dictionary of inverse properties as a JSON string, or an error message.
    """
    try:
        result = om.get_instance_inverse_properties(class_name, instance_name)
        return json.dumps(result)
    except ValueError as e:
        return str(e)

@tool
def get_all_instances_in_ontology() -> str:
    """
    Retrieve all instances across the entire ontology.

    :return: List of instance names as a JSON string, or an error message.
    """
    try:
        result = om.get_all_instances_in_ontology()
        instance_names = [inst.name for inst in result]
        return json.dumps(instance_names)
    except ValueError as e:
        return str(e)

@tool
def get_class_restrictions(class_name: str) -> str:
    """
    Retrieve all restrictions (inherited or direct) for a given class.

    :param class_name: Name of the ontology class.
    :return: List of restriction descriptions as a JSON string, or an error message.
    """
    try:
        result = om.get_class_restrictions(class_name)
        return json.dumps(result)
    except ValueError as e:
        return str(e)

@tool
def print_class_information(class_name: str) -> None:
    """
    Print information (ancestors, super classes, subclasses, properties, etc.) of an ontology class.
    """
    OntologyManager.print(class_name)


tools = [
    save, create_ontology_concept_class, get_ontology_classes_by_condition, get_ontology_class,
    get_ontology_classes_by_namespace, get_ontology_classes_by_subname, get_ontology_descendant_classes,
    create_ontology_triple_classes, create_ontology_instance, get_ontology_instance_by_name,
    get_all_ontology_instances_of_class, get_instance_properties, get_instance_inverse_properties,
    get_all_instances_in_ontology,get_class_restrictions,print_class_information
]

# 4. LLM and Tool Binding
llm = ChatOpenAI(model=LLM_MODEL, temperature=LLM_TEMPERATURE)
llm_with_tools = llm.bind_tools(tools)


# 5. Agent Node
def onto_agent(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


# 6. Tool Node
class BasicToolNode:
    def __init__(self, tools: list):
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No Message found in input")

        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}


tool_node = BasicToolNode(tools=tools)


# 7. Routing Function
def route_tools(state: dict):
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


# 8. Graph Construction
graph_builder = StateGraph(State)
graph_builder.add_node("agent", onto_agent)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges("agent", route_tools, {"tools": "tools", END: END})
graph_builder.add_edge("tools", "agent")
graph_builder.add_edge(START, "agent")
graph = graph_builder.compile()


# 9. Stream Function
def stream_graph_updates(user_input: str):
    state = {"messages": [HumanMessage(content=user_input)]}
    output = []
    for event in graph.stream(state):
        for node_output in event.values():
            if "messages" in node_output:
                messages = node_output["messages"]
                if messages:
                    last_message = messages[-1]
                    if isinstance(last_message, HumanMessage):
                        output.append(f"Human Message: {last_message.content}")
                        print(f"Human Message: {last_message.content}")
                    elif isinstance(last_message, AIMessage):
                        output.append(f"AI Message: {last_message.content}")
                        print(f"AI Message: {last_message.content}")
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            for tool_call in last_message.tool_calls:
                                output.append(f"  Tool: {tool_call['name']}")
                                output.append(f"  Tool Args: {tool_call['args']}")
                                print(f"  Tool: {tool_call['name']}")
                                print(f"  Tool Args: {tool_call['args']}")
                                tool_results = tool_node({"messages": [last_message]})
                                tool_result_message = tool_results["messages"][-1]
                                if isinstance(tool_result_message, ToolMessage):
                                    print(f"  Tool Message: {tool_result_message.content}")
                                    output.append(f"  Tool Message: {tool_result_message.content}")
                    elif isinstance(last_message, ToolMessage):
                        output.append(f"Tool Message: {last_message.content}")
                        print(f"Tool Message: {last_message.content}")
    return str(output)

#10. Direct Graph Invocation
def graph_invoke(user_input: str):
    return graph.invoke({"messages" : [HumanMessage(content=user_input)]})


# 10. Example Usage
if __name__ == "__main__":
    # inputs = input("Enter your query: ")
    # stream_graph_updates(inputs)
    print()




# class OntologyManager(object, metaclass=Singleton):
#     def __init__(self, main_ontology_iri: str = ONTOLOGY_FILE, ontology_search_path: str = f"{Path.home()}/ontologies"):
#         Path(ontology_search_path).mkdir(parents=True, exist_ok=True)
#         owlready2.onto_path.append(ontology_search_path)
#
#         self.ontologies: Dict[str, owlready2.Ontology] = {}
#         self.main_ontology: owlready2.Ontology = None
#         self.soma: owlready2.Ontology = None
#         self.dul: owlready2.Ontology = None
#         self.ontology_world: owlready2.World = None
#         self.main_ontology_iri: str = main_ontology_iri
#         self.main_ontology_namespace: owlready2.Namespace = None
#
#         self.ontology_world = World(filename=f"{ontology_search_path}/{Path(main_ontology_iri).stem}.sqlite3",
#                                     exclusive=False, enable_thread_parallelism=True)
#         self.main_ontology, self.main_ontology_namespace = self.load_ontology(main_ontology_iri)
#         if self.main_ontology.loaded:
#             self.soma = self.ontologies["SOMA"]
#             self.dul = self.ontologies["DUL"]
#
#     def load_ontology(self, ontology_iri) -> tuple[owlready2.Ontology, owlready2.Namespace] | None:
#         ontology = self.ontology_world.get_ontology(ontology_iri).load(reload_if_newer=True)
#         ontology_namespace = owlready2.get_namespace(ontology_iri)
#         if ontology.loaded:
#             def fetch_ontology(ontology__):
#                 self.ontologies[ontology__.name] = ontology__
#
#             self.browse_ontologies(ontology, condition=None, func=lambda ontology__: fetch_ontology(ontology__))
#             return ontology, ontology_namespace
#         return None
#
#     def initialized(self) -> bool:
#         return hasattr(self, "main_ontology") and self.main_ontology.loaded
#
#     @staticmethod
#     def browse_ontologies(ontology: owlready2.Ontology, condition=None, func=None, **kwargs) -> None:
#         if ontology is None or not ontology.loaded:
#             return
#         will_do_func = func is not None
#         if condition is None:
#             if will_do_func:
#                 func(ontology, **kwargs)
#                 for sub_onto in ontology.get_imported_ontologies():
#                     func(sub_onto, **kwargs)
#         elif condition(ontology, **kwargs):
#             if will_do_func: func(ontology, **kwargs)
#         else:
#             for sub_onto in ontology.get_imported_ontologies():
#                 if condition(sub_onto, **kwargs) and will_do_func:
#                     func(sub_onto, **kwargs)
#                     break
#
#     # Non-static methods converted to tools below
#     def save(self, target_filename: str = "", overwrite: bool = False) -> bool:
#         self.ontology_world.save()
#         is_current_ontology_local = Path(self.main_ontology_iri).exists()
#         current_ontology_filename = self.main_ontology_iri if is_current_ontology_local \
#             else f"{Path(self.ontology_world.filename).parent.absolute()}/{Path(self.main_ontology_iri).stem}.owl"
#         save_to_same_file = is_current_ontology_local and (target_filename == current_ontology_filename)
#         if save_to_same_file and not overwrite:
#             return False
#         else:
#             save_filename = target_filename if target_filename else current_ontology_filename
#             self.main_ontology.save(save_filename)
#             return True
#
#     # Concept Class Methods
#     def create_ontology_concept_class(self, class_name: str, ontology_parent_concept_class=None) -> Type[
#         owlready2.Thing]:
#         ontology_concept_class = self.get_ontology_class_by_ontology(self.main_ontology, class_name)
#         if ontology_concept_class:
#             return ontology_concept_class
#         with self.main_ontology:
#             return types.new_class(class_name, (owlready2.Thing, ontology_parent_concept_class,)
#             if inspect.isclass(ontology_parent_concept_class) else (owlready2.Thing,))
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
#     def get_ontology_classes_by_namespace(self, ontology_namespace: str) -> List[Type[owlready2.Thing]]:
#         def is_matching_ontology_namespace(ontology_class: Type[owlready2.Thing]):
#             return ontology_class.namespace.name == ontology_namespace
#
#         return self.get_ontology_classes_by_condition(condition="is_matching_ontology_namespace")
#
#     def get_ontology_classes_by_subname(self, class_subname: str) -> List[Type[owlready2.Thing]]:
#         def is_matching_class_subname(ontology_class: Type[owlready2.Thing]):
#             return class_subname.lower() in ontology_class.name.lower()
#
#         return self.get_ontology_classes_by_condition(condition="is_matching_class_subname")
#
#     def get_ontology_descendant_classes(self, ancestor_class_name: str, class_subname: str = "") -> List[
#         Type[owlready2.Thing]]:
#         ancestor_class = self.get_ontology_class(ancestor_class_name)
#         if not ancestor_class:
#             return []
#         return [ontology_class for ontology_class in self.main_ontology.classes()
#                 if (class_subname.lower() in ontology_class.name.lower()) and (
#                             ancestor_class in ontology_class.ancestors())]
#
#     def create_ontology_triple_classes(self, subject_class_name: str, object_class_name: str, predicate_name: str,
#                                        inverse_predicate_name: str, ontology_subject_parent_class=None,
#                                        ontology_object_parent_class=None, ontology_property_parent_class=None,
#                                        ontology_inverse_property_parent_class=None) -> None:
#         with self.main_ontology:
#             ontology_subject_class = self.create_ontology_concept_class(subject_class_name,
#                                                                         ontology_subject_parent_class)
#             ontology_object_class = self.create_ontology_concept_class(object_class_name, ontology_object_parent_class)
#             ontology_predicate_class = types.new_class("OntologyPredicate", (owlready2.ObjectProperty,))
#             ontology_predicate_class.domain = [ontology_subject_class]
#             ontology_predicate_class.range = [ontology_object_class]
#             ontology_predicate_class.python_name = predicate_name
#             ontology_inverse_predicate = types.new_class("OntologyInversePredicate", (owlready2.ObjectProperty,))
#             ontology_inverse_predicate.inverse_property = ontology_predicate_class
#             ontology_inverse_predicate.python_name = inverse_predicate_name
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
#                     inverse_properties[prop.python_name] = [val.name if hasattr(val, 'name') else str(val) for val in
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