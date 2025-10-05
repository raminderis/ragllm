from llm import llm
from graph import graph
import asyncio
from dotenv import load_dotenv


# Create a network chat chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser

chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a telecommunications network expert providing information about the network."),
        ("human", "{input}"),
    ]
)

network_chat = chat_prompt | llm | StrOutputParser()

# Create a set of tools
from langchain.tools import Tool
from tools.vector import get_network_plot
from tools.cypher import cypher_qa

import os
from network import TestType, Measurements, Path

from AgentRunner import AgentRunner

from google.adk.models.lite_llm import LiteLlm
from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

#get env setup
load_dotenv('nb.env', override=True)

# if not os.environ.get('NEO4J_URI'):
#     os.environ['NEO4J_URI'] = getpass.getpass('NEO4J_URI:\n')
# if not os.environ.get('NEO4J_USERNAME'):
#     os.environ['NEO4J_USERNAME'] = getpass.getpass('NEO4J_USERNAME:\n')
# if not os.environ.get('NEO4J_PASSWORD'):
#     os.environ['NEO4J_PASSWORD'] = getpass.getpass('NEO4J_PASSWORD:\n')

NEO4J_URI = os.getenv('NEO4J_URI') #bolt://44.201.66.214:7687
NEO4J_USERNAME = os.getenv('NEO4J_USERNAME') #neo4j
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD') #moisture-mists-influences

# $env:NEO4J_URI = "bolt://13.222.241.85:7687"
# $env:NEO4J_USERNAME = "neo4j"               

print(f"OpenAI API Key found: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")
print("openai api key:", os.getenv('OPENAI_API_KEY'))

database_agent = Agent(
    name="graph_database_agent",
    # model="gemini-2.0-flash-exp",
    model=LiteLlm(model="openai/gpt-4.1"),
    # model=LiteLlm(model="anthropic/claude-sonnet-4-20250514"),
    description="""
    Agent to access knowledge graph stored in graph database
    """,
    instruction=f"""
    You are a human resources assistant who helps with network entity information about its location, configuration, coordinates, health analysis, ping and twamp KPI results over near, far and rt paths, and report on different types of KPIs like composite, jitter, delay and latency.

    You can access the knowledge (in a graph database) on att network ping and twamp KPI results based on their KPI results on jitter, delay, latency produced by either PING and TWAMP test cases against network entities over either near path or far path or rt path.  ALWAYS get the schema first with `get_schema` and keep it in memory. Only use node labels, relationship types, and property names, and patterns in that schema to generate valid Cypher queries using the `read_neo4j_cypher` tool with proper parameter syntax ($parameter). If you get errors or empty results check the schema and try again at least up to 3 times.

    For domain knowledge, use these standard values:
    - TestType: {[i.value for i in TestType]}
    - Measurements: {[i.value for i in Measurements]}
    - Path: {[i.value for i in Path]}

    Also never return embedding properties in Cypher queries. This will result in delays and errors.

    When responding to the user:
    - if your response includes netowkr entity, include there entity_id.
    - You must explain your retrieval logic and where the data came from. You must say exactly how relevance, similarity, etc. was inferred during search.

    Use information from previous queries when possible instead of asking the user again.
    """,
    tools=[MCPToolset(
        connection_params=StdioServerParameters(
            command='uvx',
            args=[
                "mcp-neo4j-cypher",
            ],
            env={ k: os.environ[k] for k in ["NEO4J_URI","NEO4J_USERNAME","NEO4J_PASSWORD"] }
        ),
        tool_filter=['get_neo4j_schema','read_neo4j_cypher']
    )]
)

db_agent_runner = AgentRunner(app_name='db_agent', user_id='Mr. Ed', agent=database_agent)

async def ensure_session_then_run(runner):
    if not runner.session or not getattr(runner.session, "id", None):
        print("XXXXX NOOOOO SESSION FOUND. Will Start session XXXXX")
        await runner.start_session()
        
async def sync_tool(query: str):
    await ensure_session_then_run(db_agent_runner)
    return await db_agent_runner.run(query)

    # return sync_wrapper(ensure_session_then_run, query)

def blocking_async_wrapper(coro):
    """
    A synchronous wrapper that safely runs and awaits a coroutine.
    """
    try:
        loop = asyncio.get_running_loop()
        # If a loop is running, run the coroutine until it completes.
        return loop.run_until_complete(coro)
    except RuntimeError:
        # If no loop is running (e.g., in a script), create and run one.
        return asyncio.run(coro)

def run_query_sync(query: str):
    return blocking_async_wrapper(sync_tool(query))

# def sync_wrapper(coro_func, *args, **kwargs):
#     try:
#         loop = asyncio.get_event_loop()
#         if loop.is_running():
#             return asyncio.ensure_future(coro_func(*args, **kwargs))
#         else:
#             return loop.run_until_complete(coro_func(*args, **kwargs))
#     except RuntimeError:
#         # Fallback: create new loop
#         new_loop = asyncio.new_event_loop()
#         asyncio.set_event_loop(new_loop)
#         return new_loop.run_until_complete(coro_func(*args, **kwargs))


tools = [
    # Tool.from_function(
    #     name="General Chat",
    #     description="For general network chat not covered by other tools.",
    #     func=network_chat.invoke,
    # ),
    Tool.from_function(
        name="Network Plot Search",
        description="For when you need to find network test results in the network.",
        func=get_network_plot,
    ),
    # Tool.from_function(
    #     name="Network Information",
    #     description="Provide information about network questions and root cause analysis using Cypher queries.",
    #     func=run_query_sync
    # ),
    Tool.from_function(
        name="Ping Information",
        description="Use this to answer ICMP or ping protocol questions by querying network knowledge (e.g., how ping works, what an Echo Request is, reason for failure).",
        func=run_query_sync
    ),
    Tool.from_function(
        name="Network Information and Test Creation",
        #description="For when you need to find network entity information like names, locations, markets, city located in the network. Treat whole query as input not just entity names.",
        description="Use this tool to process the full user query and extract network entity information regarding network health, entity, logs, standard documentation, test payload creation. Always pass the entire query string, not just the entity name.",
        func=run_query_sync
    )
]

# Create chat history callback
from langchain_neo4j import Neo4jChatMessageHistory

def get_memory(session_id):
    return Neo4jChatMessageHistory(
        session_id=session_id,
        graph=graph
    )
# Create the agent
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain import hub
from langchain_core.prompts import PromptTemplate


#agent_prompt = hub.pull("hwchase17/react-chat")
agent_prompt = PromptTemplate.from_template("""
You are a telecommunication network expert providing information about network and network health.
Be as helpful as possible and return as much information as possible. 
Use prior retrieved context whenever possible before calling external tools.
                                            
Always pass the user's entire question as the `Action Input`, not just a named entity. 
For example, if the user asks "What is the health of sfo_amf_1?", use exactly that as the input — not just "sfo_amf_1".
                                            
Ignore trailing punctuation like question marks in input normalization. Treat "What is the health of amf_dallas_1?" and "What is the health of amf_dallas_1" identically.


                                            
Important: You must always produce either a response from retrieved context or a tool invocation followed by your own knowledge using the full format, or a Final Answer using the specified format. Any other response will break the system.


TOOLS:
------

You have access to the following tools:
{tools}
To use a tool, please use the following format:
Thought: Do I need to use a tool? Yes
Action: The action to take, should be one of [{tool_names}]
Action Input: The input to the action
Observation: The result of the action

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
Thought: Do I need to use a tool? No
Final Answer: [your response here]

Begin!
Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}                                            
""")
agent = create_react_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)
chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Create a handler to call the agent
from utils import get_session_id
from langchain.callbacks import get_openai_callback

def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """
    # Invoke the agent with the user input
    with get_openai_callback() as cb:
        # response = chat_agent.invoke({'input': user_input}, {'configurable': {'session_id': "123"}})
        response = chat_agent.invoke({'input': user_input}, {'configurable': {'session_id': get_session_id()}})
        print("Prompt exchange between Langchain and LLM Tokens: ", cb.prompt_tokens)
        print("Completion Tokens consumed by LLM: ", cb.completion_tokens)
        print("Total Tokens: ", cb.total_tokens)
        print("Cost: ", cb.total_cost)
    return response['output']



