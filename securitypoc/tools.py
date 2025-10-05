from neo4j import GraphDatabase

def cypher_security_tool(query: str, uri: str, user: str, password: str) -> str:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run(query)
        records = [record.data() for record in result]
    driver.close()
    return f"Returned {len(records)} records:\n{records}"
