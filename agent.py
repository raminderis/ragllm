from llm import llm
from graph import graph

# Create a movie chat chain
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
from tools.vector import get_movie_plot
from tools.cypher import cypher_qa

tools = [
    # Tool.from_function(
    #     name="General Chat",
    #     description="For general network chat not covered by other tools.",
    #     func=network_chat.invoke,
    # ),
    Tool.from_function(
        name="Network Plot Search",
        description="For when you need to find network test results in the network.",
        func=get_movie_plot,
    ),
    Tool.from_function(
        name="Network Information",
        description="Provide information about network questions and root cause analysis using Cypher queries.",
        func=get_movie_plot
    ),
    Tool.from_function(
        name="Ping Information",
        description="Use this to answer ICMP or ping protocol questions by querying network knowledge (e.g., how ping works, what an Echo Request is, reason for failure).",
        func=get_movie_plot
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
Be as helpful as possible and return as much information as possible but only from the tools provided.
                                            
Always pass the user's entire question as the `Action Input`, not just a named entity. 
For example, if the user asks "What is the health of sfo_amf_1?", use exactly that as the input — not just "sfo_amf_1".
                                            
Never rely on your own knowledge. If no tool is appropriate, respond with: 'I don't know based on the available information.'
                                            
Do not answer any questions that do not relate to networks, ping results, or cause of test failures. 
Use known error indicators (e.g., power failure, database lookup failure) to infer root cause. If multiple are present, prioritize those affecting system state directly (power > CPU > DB).


Do not answer questions using your pre-trained knowledge, only use the information provided in the context.                                                                                        

TOOLS:
------

You have access to the following tools:
{tools}
To use a tool, please use the following format:
```
Thought: Do I need to use a tool? Yes
Action: The action to take, should be one of [{tool_names}]
Action Input: The input to the action
Observation: The result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:
```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

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
    verbose=True
)
chat_agent = RunnableWithMessageHistory(
    agent_executor,
    get_memory,
    input_messages_key="input",
    history_messages_key="chat_history",
)

# Create a handler to call the agent
from utils import get_session_id

def generate_response(user_input):
    """
    Create a handler that calls the Conversational agent
    and returns a response to be rendered in the UI
    """
    # Invoke the agent with the user input
    response = chat_agent.invoke({'input': user_input}, {'configurable': {'session_id': get_session_id()}})
    return response['output']