import re

from groq import Groq

from src.config.settings import Settings


class CypherGenerator:
    def __init__(self, settings: Settings):

        self.client = Groq(
            api_key=settings.groq_api_key
        )

        self.model = "openai/gpt-oss-120b"

    # ----------------------------------
    # GENERATE CYPHER QUERY
    # ----------------------------------

    def generate(self, question: str) -> str:

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": """
You are a Neo4j Cypher query generator.

The database uses this schema:

1. Entity nodes:
   (:Entity {
       id,
       name,
       entity_type,
       description
   })

2. Relationships:
   (:Entity)-[:RELATED_TO {
       type,
       description
   }]->(:Entity)

3. Document nodes:
   (:Document {id, ...})

4. Chunk nodes:
   (:Chunk {
       id,
       text,
       page_number,
       chunk_index,
       embedding
   })

5. Document contains chunks:
   (:Document)-[:CONTAINS]->(:Chunk)

6. Chunks mention entities:
   (:Chunk)-[:MENTIONS]->(:Entity)

RULES:

1. Generate only read-only Cypher queries.
2. Use MATCH and OPTIONAL MATCH for retrieval.
3. Never use CREATE, MERGE, DELETE, SET, REMOVE,
   DROP, ALTER, CALL, LOAD CSV, or administrative commands.
4. Do not modify the database.
5. Use only the schema provided above.
6. Return only the Cypher query.
7. Do not use Markdown code fences.
8. Limit results to a maximum of 50 records.
"""
                },
                {
                    "role": "user",
                    "content": question
                }
            ],

            temperature=0
        )

        query = response.choices[0].message.content.strip()

        return query

    # ----------------------------------
    # VALIDATE CYPHER QUERY
    # ----------------------------------

    def validate(self, query: str) -> bool:

        if not query:
            return False

        # Reject multiple queries
        if ";" in query:
            return False

        # Reject comments
        if "//" in query or "/*" in query or "*/" in query:
            return False

        # Reject dangerous keywords
        forbidden_keywords = [
            "CREATE",
            "MERGE",
            "DELETE",
            "DETACH",
            "SET",
            "REMOVE",
            "DROP",
            "ALTER",
            "CALL",
            "LOAD",
            "FOREACH",
            "GRANT",
            "DENY",
            "REVOKE",
            "TERMINATE",
            "START",
            "STOP"
        ]

        words = re.findall(
            r"\b[A-Za-z_]+\b",
            query.upper()
        )

        if any(word in forbidden_keywords for word in words):
            return False

        # Only allow read-oriented query starts
        if not re.match(
            r"^\s*(MATCH|OPTIONAL\s+MATCH|WITH)\b",
            query,
            re.IGNORECASE
        ):
            return False

        # Require a return statement
        if not re.search(
            r"\bRETURN\b",
            query,
            re.IGNORECASE
        ):
            return False

        return True
