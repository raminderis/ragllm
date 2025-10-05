import streamlit as st
from llm import llm, embeddings
from graph import graph
from tools.graph_parser import GraphParser

# Create the Neo4jVector
from langchain_neo4j import Neo4jVector

neo4jentityvector = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="entity",
    node_label="ENTITY",
    text_node_property="metaDataText",
    embedding_node_property="embedding",
    retrieval_query="""
RETURN
    node.metaDataText AS text,
    score,
    {
        Name: node.name_id,
        Latitude: node.latitude,
        Longitude: node.longitude,
        EntityGroup: node.entity_group
    }AS metadata
"""
)

neo4jkpivector = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="kpi",
    node_label="KPI",
    text_node_property="perfDataText",
    embedding_node_property="embedding",
    retrieval_query="""
RETURN
    node.perfDataText AS text,
    score,
    {
        EntityKey: node.entity_key,
        Address: node.target_address,
        Qos: node.qos,
        Att_delay_rt_max: node.att_delay_rt_max,
        Att_delay_rt_min: node.att_delay_rt_min,
    }AS metadata
"""
)

# neo4jamfvector = Neo4jVector.from_existing_index(
#     embeddings,
#     graph=graph,
#     index_name="amf",
#     node_label="AMF",
#     text_node_property="amfPlot",
#     embedding_node_property="embedding",
#     retrieval_query="""
# RETURN
#     node.amfPlot AS text,
#     score,
#     {
#         Name: node.Name,
#         Location: node.Location,
#         Technology: node.Technology,
#         Market: node.Market
#     }AS metadata
# """
# )

# neo4jlogvector = Neo4jVector.from_existing_index(
#     embeddings,
#     graph=graph,
#     index_name="logchunk",
#     node_label="LogChunk",
#     text_node_property="message",
#     embedding_node_property="embedding",
#     retrieval_query="""
# RETURN
#     node.message AS text,
#     score,
#     {
#         datetime: node.datetime
#     }AS metadata
# """
# )

# neo4jvector = Neo4jVector.from_existing_index(
#     embeddings,
#     graph=graph,
#     index_name="testresult",
#     node_label="TESTRESULT",
#     text_node_property="resultPlot",
#     embedding_node_property="embedding",
#     retrieval_query="""
# RETURN
#     node.resultPlot AS text,
#     score,
#     {
#         name: node.name
#     }AS metadata
# """
# )

# neo4jvectorPingText = Neo4jVector.from_existing_index(
#     embeddings,
#     graph=graph,
#     index_name="pingtext",
#     node_label="StandardDocChunk",
#     text_node_property="content",
#     embedding_node_property="embedding",
#     retrieval_query="""
# RETURN
#     node.content AS text,
#     score,
#     {
#         Section: node.section
#     }AS metadata
# """
# )

# Create the node retriever
# amfretriever = neo4jamfvector.as_retriever()
neo4jentityvector = neo4jentityvector.as_retriever()
neo4jkpivector = neo4jkpivector.as_retriever()
# Create the retriever
# retriever = neo4jvector.as_retriever()
# Create the retriever for pingtext
# retrieverPingText = neo4jvectorPingText.as_retriever()
# create the retriever for logs
# logretriever = neo4jlogvector.as_retriever()

# Create the prompt
from langchain_core.prompts import ChatPromptTemplate

instructions = (
    "Use the given context to answer the question."
    "Do not use prior knowledge, only use the context provided."
    "If the context does not contain the answer, say you dont know."
    "If you dont know the answer, say you dont know."
    "Context: {context}"
)
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", instructions),
        ("human", "{input}"),
    ]
)

import tiktoken
def count_embedding_tokens(text: str, model: str) -> int:
    """
    Count the number of tokens in a text string using the OpenAI tokenizer.
    """
    encoding = tiktoken.encoding_for_model(model)
    return len(encoding.encode(text))

# Create the chain 
from langchain_core.runnables import Runnable
from typing import List, Optional
class RouterRetriever(Runnable):
    # def __init__(self, amfretriever, retriever, retrieverPingText, logretriever, neo4jkpivector, neo4jentityvector):
    def __init__(self, neo4jkpivector, neo4jentityvector):
        # self.retriever = retriever
        # self.retrieverPingText = retrieverPingText
        # self.amfretriever = amfretriever
        # self.logretriever = logretriever
        self.neo4jkpivector = neo4jkpivector
        self.neo4jentityvector = neo4jentityvector

    def invoke(self, input, config=None, **kwargs):
        print("input and retriver_list: ", input["input"], input["retriver_list"])
        total_embedding_tokens = 0
        if not input["retriver_list"]:
            print("RouterRetriever invoked with input: ", input["input"])
            query = input["input"] if isinstance(input, dict) else input
            q = query.lower()
            if any(k in q for k in ["status", "health", "result", "test", "latency"]):
                print ("Test result retriever invoked")
                embedding_tokens = count_embedding_tokens(query, embeddings.model)
                total_embedding_tokens += embedding_tokens
                print("XXX Embedding tokens within retriever: ", embedding_tokens)
                return self.neo4jkpivector.get_relevant_documents(query)
            # elif any(k in q for k in ["log", "logs", "log message", "log entry", "log file", "rootcause", "error", "issue"]):
            #     print("Log retriever invoked")
            #     embedding_tokens = count_embedding_tokens(query, embeddings.model)
            #     total_embedding_tokens += embedding_tokens
            #     print("XXX Embedding tokens within logretriever: ", embedding_tokens)
            #     return self.logretriever.get_relevant_documents(query)
            elif any(k in q for k in ["amf", "node", "display_name", "location", "entity", "market", "deployed"]):
                print("Entity retriever invoked")
                embedding_tokens = count_embedding_tokens(query, embeddings.model)
                total_embedding_tokens += embedding_tokens
                print("XXX Embedding tokens within amfretriever: ", embedding_tokens)
                return self.neo4jentityvector.get_relevant_documents(query)
            else:
                print(f"Cant find a suitable retriver will do entity retriever")
                return self.neo4jentityvector.get_relevant_documents(query)
            # elif any(k in q for k in ["icmp", "ping", "protocol", "echo request", "what is", "explain", "why"]):
            #     print("Ping retriever invoked")
            #     embedding_tokens = count_embedding_tokens(query, embeddings.model)
            #     total_embedding_tokens += embedding_tokens
            #     print("XXX Embedding tokens within retrieverPingText: ", embedding_tokens)
            #     return self.retrieverPingText.get_relevant_documents(query)
        else:
            print("RouterRetriever invoked with retriever list: ", input["retriver_list"])
            query = input["input"] if isinstance(input, dict) else input
            results = []
            for retriever_name in input["retriver_list"]:
                if retriever_name == "neo4jentityvector":
                    embedding_tokens = count_embedding_tokens(query, embeddings.model)
                    total_embedding_tokens += embedding_tokens
                    print("XXX Embedding tokens within neo4jentityvector: ", embedding_tokens)
                    results.extend(self.amfretriever.get_relevant_documents(query))
                elif retriever_name == "neo4jkpivector":
                    embedding_tokens = count_embedding_tokens(query, embeddings.model)
                    total_embedding_tokens += embedding_tokens
                    print("XXX Embedding tokens within neo4jkpivector: ", embedding_tokens)
                    results.extend(self.retriever.get_relevant_documents(query))
                
                # elif retriever_name == "retrieverPingText":
                #     embedding_tokens = count_embedding_tokens(query, embeddings.model)
                #     total_embedding_tokens += embedding_tokens
                #     print("XXX Embedding tokens within retrieverPingText: ", embedding_tokens)
                #     results.extend(self.retrieverPingText.get_relevant_documents(query))
                # elif retriever_name == "logretriever":
                #     embedding_tokens = count_embedding_tokens(query, embeddings.model)
                #     total_embedding_tokens += embedding_tokens
                #     print("XXX Embedding tokens within logretriever: ", embedding_tokens)
                #     results.extend(self.logretriever.get_relevant_documents(query))
            print("Total embedding tokens: ", total_embedding_tokens)
            print(f"Total embedding cost estimate: {(total_embedding_tokens / 1000) * 0.0001 : .10f} USD")
            return results
        # else:
        #     return (
        #         self.amfretriever.get_relevant_documents(query)
        #         + self.retriever.get_relevant_documents(query)
        #         + self.retrieverPingText.get_relevant_documents(query)
        #         + self.logretriever.get_relevant_documents(query)
        #     )

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
# question_answer_chain = create_stuff_documents_chain(llm, prompt)
from langchain_core.output_parsers import StrOutputParser

question_answer_chain = create_stuff_documents_chain(
    llm,
    prompt
).with_config(output_parser=StrOutputParser())


# router_retriever = RouterRetriever(amfretriever, retriever, retrieverPingText, logretriever)
router_retriever = RouterRetriever(neo4jkpivector, neo4jentityvector)
plot_retriver = create_retrieval_chain(
    router_retriever,
    question_answer_chain
)
# Create a function to call the chain
import nltk
import string

nltk.download('stopwords')
from nltk.corpus import stopwords
def get_network_plot(input):
    print("get_network_plot called with input: ", input)
    input = input.strip().rstrip(string.punctuation)
    print("get_network_plot called with input without punctuation: ", input)
    stop_words = set(stopwords.words("english"))
    tokens = input.lower().split()
    filtered_tokens = [t for t in tokens if t not in stop_words]
    normalized_query = " ".join(filtered_tokens)
    print("Normalized query: ", normalized_query)
    parser = GraphParser(
        uri=st.secrets["NEO4J_URI"],
        user=st.secrets["NEO4J_USERNAME"],
        password=st.secrets["NEO4J_PASSWORD"]
    )
    print("Parser created with URI: ", st.secrets["NEO4J_URI"])
    print("User: ", st.secrets["NEO4J_USERNAME"])
    print("Password: ", st.secrets["NEO4J_PASSWORD"])
    print("Graph: ", graph)
    retrieval_plan = parser.get_retrieval_plan(normalized_query.split(" "))
    print("Retrieval plan: ", retrieval_plan)
    if not retrieval_plan["retrivers_to_activate"]:
        print("No retrievers to activate, returning empty list")
        return plot_retriver.invoke({"input": normalized_query,"retriver_list": None})
    else:
        print("Retrievers to activate: ", retrieval_plan["retrivers_to_activate"])
        retrivers = retrieval_plan["retrivers_to_activate"]
        return plot_retriver.invoke({"input": normalized_query,"retriver_list": retrieval_plan["retrivers_to_activate"]})
    # return plot_retriver.invoke(
    #     {"input": normalized_query}
    # )