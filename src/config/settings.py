import os
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        load_dotenv()
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_username = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_database = os.getenv("NEO4J_DATABASE")
        self.groq_api_key = os.getenv("GROQ_API_KEY")

