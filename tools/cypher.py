import streamlit as st
from llm import llm
from graph import graph
from langchain_neo4j import GraphCypherQAChain

# Create the Cypher prompt template
from langchain.prompts.prompt import PromptTemplate

CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Developer translating user questions into Cypher to answer questions about network especially AMFs and test agents executing ping tests against those AMFs.
You should be able to provide their location, test results, targets, reason for failure by looking at logs for dallas_amf_1 and ping documentation explanation. 

Your Cypher output must follow these rules:
- Only return **one complete Cypher query**
- Only generate Cypher queries related to the question explicitly asked.
- Do not generate multiple top-level MATCH or RETURN clauses
- Combine steps using WITH, UNION, or nested subqueries if needed
- Use only the provided relationship types and properties from the schema
- Do not return entire nodes or embedding properties


Schema:
{schema}

Question:
{question}

Cypher Query:
"""

cypher_prompt = PromptTemplate.from_template(CYPHER_GENERATION_TEMPLATE)

# Create the Cypher QA chain


cypher_qa = GraphCypherQAChain.from_llm(
    llm,
    graph=graph,
    verbose=True,
    cypher_prompt=cypher_prompt,
    allow_dangerous_requests=True
)


