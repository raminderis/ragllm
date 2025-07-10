import streamlit as st
from llm import llm, embeddings
from graph import graph

# Create the Neo4jVector
from langchain_neo4j import Neo4jVector



neo4jamfvector = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="amf",
    node_label="AMF",
    text_node_property="amfPlot",
    embedding_node_property="embedding",
    retrieval_query="""
RETURN
    node.amfPlot AS text,
    score,
    {
        Name: node.Name,
        Location: node.Location,
        Technology: node.Technology,
        Market: node.Market
    }AS metadata
"""
)

neo4jlogvector = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="logchunk",
    node_label="LogChunk",
    text_node_property="message",
    embedding_node_property="embedding",
    retrieval_query="""
RETURN
    node.message AS text,
    score,
    {
        datetime: node.datetime
    }AS metadata
"""
)

neo4jvector = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="testresult",
    node_label="TESTRESULT",
    text_node_property="resultPlot",
    embedding_node_property="embedding",
    retrieval_query="""
RETURN
    node.resultPlot AS text,
    score,
    {
        name: node.name
    }AS metadata
"""
)

neo4jvectorPingText = Neo4jVector.from_existing_index(
    embeddings,
    graph=graph,
    index_name="pingtext",
    node_label="StandardDocChunk",
    text_node_property="content",
    embedding_node_property="embedding",
    retrieval_query="""
RETURN
    node.content AS text,
    score,
    {
        Section: node.section
    }AS metadata
"""
)

# Create the node retriever
amfretriever = neo4jamfvector.as_retriever()
# Create the retriever
retriever = neo4jvector.as_retriever()
# Create the retriever for pingtext
retrieverPingText = neo4jvectorPingText.as_retriever()
# create the retriever for logs
logretriever = neo4jlogvector.as_retriever()

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

# Create the chain 
from langchain_core.runnables import Runnable
class RouterRetriever(Runnable):
    def __init__(self, amfretriever, retriever, retrieverPingText, logretriever):
        self.retriever = retriever
        self.retrieverPingText = retrieverPingText
        self.amfretriever = amfretriever
        self.logretriever = logretriever

    def invoke(self, input: str, config=None, **kwargs):
        print("RouterRetriever invoked with input: ", input)
        query = input["input"] if isinstance(input, dict) else input
        q = query.lower()
        print("Raminder: " , q)
        if any(k in q for k in ["status", "health", "result", "test", "latency"]):
            print ("Test result retriever invoked")
            return self.retriever.get_relevant_documents(query)
        elif any(k in q for k in ["amf", "node", "where", "location", "technology", "market", "deployed"]):
            print("AMF retriever invoked")
            return self.amfretriever.get_relevant_documents(query)
        elif any(k in q for k in ["icmp", "ping", "protocol", "echo request", "what is", "explain", "why"]):
            print("Ping retriever invoked")
            return self.retrieverPingText.get_relevant_documents(query)
        elif any(k in q for k in ["log", "logs", "log message", "log entry", "log file", "root cause", "error", "issue"]):
            print("Log retriever invoked")
            return self.logretriever.get_relevant_documents(query)
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


router_retriever = RouterRetriever(amfretriever, retriever, retrieverPingText, logretriever)
plot_retriver = create_retrieval_chain(
    router_retriever,
    question_answer_chain
)
# Create a function to call the chain
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
def get_movie_plot(input):
    print("get_movie_plot called with input: ", input)
    
    stop_words = set(stopwords.words("english"))
    tokens = input.lower().split()
    filtered_tokens = [t for t in tokens if t not in stop_words]
    normalized_query = " ".join(filtered_tokens)
    print("Normalized query: ", normalized_query)
    return plot_retriver.invoke(
        {"input": normalized_query}
    )