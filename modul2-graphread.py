import getpass
import os
from dotenv import load_dotenv

from network import TestType, Measurements, Path

from AgentRunner import AgentRunner
# build adk agent with neo4j mcp

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

import asyncio


async def start():
    await db_agent_runner.start_session()
    # res = await db_agent_runner.run("what do you know about the health of FRLDNJHUB00002 or entities that have this in its name?")
    res = await db_agent_runner.run("what do you know about the entity of FRLDNJHUB00002 or entities that have this in its name?")
    
    print(res)

    # res2 = await db_agent_runner.run("which test config was used for the twamp test case run against 414088?")
    # print(res2)

    # res3 = await db_agent_runner.run("what time was ping test run against entity 157487?")
    # print(res3)

    # res4 = await db_agent_runner.run("what time was twamp test run against entity 157487?")
    # print(res4)


asyncio.run(start())
