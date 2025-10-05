from google.adk.agents import LlmAgent
from google.genai import types
import os
from tools import cypher_security_tool
from google.adk.tools import FunctionTool

from neo4j import GraphDatabase

cypher_tool_decl = types.FunctionDeclaration(
    name="cypher_security_tool",
    description="Run Cypher queries for network anomaly and security insights.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "uri": {"type": "string"},
            "user": {"type": "string"},
            "password": {"type": "string"}
        },
        "required": ["query"]
    }
)

def cypher_security_tool(query: str) -> str:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    print("cypher secuiryt tool")
    if not all([uri, user, password]):
        # Handle case where environment variables are missing
        return "ERROR: Database connection details are not configured."
    print("Executing Cypher query...")
    try:
    # Run query logic here...
        driver = GraphDatabase.driver(uri, auth=(user, password))
        with driver.session() as session:
            result = session.run(query)
            return "\n".join(str(record.data()) for record in result)
    except Exception as e:
        return f"Database Query Error: {e}"
    
cypher_tool = FunctionTool(
    func=cypher_security_tool
)

agent = LlmAgent(
    name="network_security_agent",
    model="gemini-2.0-flash",
    instruction="""
    You are a network security expert. Use the cypher_security_tool to detect anomalies, trace suspicious entities, and explain your reasoning clearly.
    Always include the Cypher logic used and describe how relevance was inferred.
    
    Graph Schema for Network Security:**
    - **Nodes:**
        - **:User** (properties: `username`, `homeCountry`)
        - **:Session** (properties: `sessionId`, `startTime`, `endTime`, `status`)
        - **:IP_Address** (properties: `address`)
        - **:GeoLocation** (properties: `country`)
        - **:Device** (properties: `deviceId`)
        - **:NetworkSegment** (properties: `segmentId`, `sensitivity`)
    - **Relationships:**
        - `(:User)-[:INITIATED_SESSION]->(:Session)`
        - `(:Session)-[:FROM_IP]->(:IP_Address)`
        - `(:IP_Address)-[:BELONGS_TO]->(:GeoLocation)`
        - `(:Session)-[:USED_DEVICE]->(:Device)`
        - `(:User)-[:USES_DEVICE]-(:Device)`
        - `(:Session)-[:CONNECTED_TO]->(:Segment)`
        - `(:User)-[:LOGGED_IN_FROM]->(:IP_Address)` (for tracing origin)
        
    **Rule:** Always respond with a security insight and include the Cypher logic you generated and executed. Try to use Cypher queries that adhere to the provided schema.
    """,
    tools=[cypher_tool]
#     tool_implementations = {
#     "cypher_security_tool": lambda: cypher_security_tool(
#         query="""
#         MATCH (u:User)-[:INITIATED_SESSION]->(s:Session)-[:FROM_IP]->(ip:IP_Address),
#               (ip)-[:BELONGS_TO]->(geo:GeoLocation),
#               (s)-[:USED_DEVICE]->(d:Device),
#               (s)-[:CONNECTED_TO]->(seg:Segment),
#               (u)-[:LOGGED_IN_FROM]->(ip)
#         RETURN u.username AS user,
#                s.sessionId AS session,
#                ip.address AS ip,
#                geo.name AS country,
#                d.deviceId AS device,
#                seg.name AS segment
#         """,
#         uri=os.getenv("NEO4J_URI"),
#         user=os.getenv("NEO4J_USERNAME"),
#         password=os.getenv("NEO4J_PASSWORD")
#     )
# }
)
