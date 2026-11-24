from src.graph.neo4j_connection import Neo4jConnection

class ChunkReader:

    def __init__(self, connection: Neo4jConnection):
        self.driver = connection.driver

    def get_all_chunks(self):
        query = """
        MATCH (c:Chunk)
        RETURN
            c.id AS chunk_id,
            c.text AS text,
            c.page_number AS page_number
        ORDER BY c.chunk_index
        """

        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

    
    def get_unprocessed_chunks(self):
        query = """
        MATCH (c:Chunk)
        WHERE NOT (c)-[:MENTIONS]->()
        RETURN
            c.id AS chunk_id,
            c.text AS text,
            c.page_number AS page_number
        ORDER BY c.chunk_index
        """

        with self.driver.session() as session:
            result = session.run(query)
            return [record.data() for record in result]

