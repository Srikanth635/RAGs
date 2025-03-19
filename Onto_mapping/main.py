from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage
from typing import Dict, List, Any
from tools import OntologyTools
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents.format_scratchpad.openai_tools import format_to_openai_tool_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
import operator

#Initialize Variables.
ontology_tools = OntologyTools("SOMA.owl")
llm = ChatOpenAI(model="gpt-3.5-turbo-1106")
tool_executor = ToolExecutor(tools=[
    Tool.from_function(
        func=ontology_tools.find_relevant_classes,
        name="find_relevant_classes",
        description="Finds classes relevant to the user query."
    )
])

#Prompt.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that uses provided tools to answer user questions."),
    ("user", "{input}"),
    ("assistant", "{tools}"),
])

#Agent.
agent = {
    "input": lambda x: x["messages"],
    "tools": lambda x: format_to_openai_tool_messages(x["intermediate_steps"]),
    "messages": operator.itemgetter("messages")
} | prompt | llm.bind_tools(tool_executor.tools) | OpenAIToolsAgentOutputParser()

#Nodes.
def agent_node(state: Dict):
    result = agent.invoke(state)
    return {"messages": [result], "intermediate_steps": [result]}

def tool_node(state: Dict):
    result = tool_executor.invoke(state["messages"][-1])
    return {"messages": [result]}

def should_use_tool(state: Dict):
    if state["messages"][-1].tool_calls:
        return "tool"
    else:
        return "end"

#Graph.
workflow = StateGraph(Any)
workflow.add_node("agent", agent_node)
workflow.add_node("tool", tool_node)
workflow.add_conditional_edges("agent", should_use_tool, {"tool": "tool", "end": "end"})
workflow.add_edge("tool", "agent")
workflow.set_entry_point("agent")
chain = RunnableWithMessageHistory(workflow.compile(), get_session_history=lambda session_id: [])

#Run.
inputs = {"messages": [HumanMessage(content="What are the concepts related to grasping?")]}
result = chain.invoke(inputs, config={"configurable": {"session_id": "<foo>"}})
print(result)