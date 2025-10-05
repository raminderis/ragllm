from neo4j import GraphDatabase

class GraphParser:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_retrieval_plan(self, tokens: list[str]) -> dict:
        print("get_retrieval_plan called with tokens: ", tokens)
        with self.driver.session() as session:
            matched_nodes = session.run("""
                UNWIND $tokens AS word
                MATCH (n)
                WHERE toLower(n.Name) CONTAINS toLower(word)
                RETURN DISTINCT labels(n) AS node_labels, id(n) AS node_id                      
            """, {"tokens": tokens})
            print("Matched nodes: ", matched_nodes)
            triggered_labels = set()
            node_ids = []
            for record in matched_nodes:
                print("Node labels: ", record["node_labels"])
                print("Node IDs: ", record["node_id"])
                node_ids.append(record["node_id"])
                triggered_labels.update(record["node_labels"])
            
            related = session.run("""
                MATCH (n)-[r]-(m)
                WHERE id(n) IN $node_ids
                RETURN DISTINCT labels(m) AS related_labels, type(r) AS rel_type
                """, {"node_ids": node_ids})
            print("Related nodes: ", related)
            
            
            for record in related:
                print("Related labels: ", record["related_labels"])
                triggered_labels.update(record["related_labels"])

            retriver_map = {
                "AMF": "amfretriever",
                "StandardDoc": "retrieverPingText",
                "LogRoot": "logretriever",
                "TESTRESULT": "retriever"
            }

            active_retrivers = {
                retriver_map[label] for label in triggered_labels if label in retriver_map
            }
            print("Triggered labels: ", triggered_labels)
            print("Active retrievers: ", active_retrivers)
            return {
                "triggered_labels": list(triggered_labels),
                "retrivers_to_activate": list(active_retrivers)
            }
        