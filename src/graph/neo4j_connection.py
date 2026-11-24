from neo4j import GraphDatabase
from src.config.settings import Settings

class Neo4jConnection:
    def __init__(self, settings = Settings):
        if settings is None:
            settings = Settings()

        self.database = settings.neo4j_database

        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(
                settings.neo4j_username,
                settings.neo4j_password
            )
        )

    def verify_connection(self):
        self.driver.verify_connectivity()
        print("Connection to Neo4j database verified successfully.")
    def close(self):
        self.driver.close()
        print("Connection to Neo4j database closed.")
    