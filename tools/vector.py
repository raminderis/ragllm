import streamlit as st
from llm import llm, embeddings
from graph import graph

# Create the Neo4jVector
from langchain_neo4j import Neo4jVector

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
        title: node.name,
        target: [ (node)-[:TARGETS]->(amf) | amf.name ]
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
        title: node.name,
        target: [ (parent)-[:PART_OF]->(node) | node.name ]
    }AS metadata
"""
)

# Create the retriever
retriever = neo4jvector.as_retriever()
# Create the retriever for pingtext
retrieverPingText = neo4jvectorPingText.as_retriever()

# Create the prompt
from langchain_core.prompts import ChatPromptTemplate

instructions = (
    "Use the given context to answer the question."
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
    def __init__(self, retriever, retrieverPingText):
        self.retriever = retriever
        self.retrieverPingText = retrieverPingText

    def invoke(self, input: str, config=None, **kwargs):
        query = input["input"] if isinstance(input, dict) else input
        q = query.lower()
        if any(k in q for k in ["status", "health", "amf", "result", "test", "latency", "packet loss"]):
            return self.retriever.get_relevant_documents(query)
        elif any(k in q for k in ["icmp", "ping", "protocol", "echo request", "what is", "explain"]):
            return self.retrieverPingText.get_relevant_documents(query)
        else:
            return (
                self.retriever.get_relevant_documents(query)
                + self.retrieverPingText.get_relevant_documents(query)
            )

from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
question_answer_chain = create_stuff_documents_chain(llm, prompt)
router_retriever = RouterRetriever(retriever, retrieverPingText)
plot_retriver = create_retrieval_chain(
    router_retriever,
    question_answer_chain
)
# Create a function to call the chain
def get_movie_plot(input):
    return plot_retriver.invoke(
        {"input": input}
    )