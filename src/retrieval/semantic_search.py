
from sentence_transformers import SentenceTransformer

from src.graph.neo4j_connection import Neo4jConnection


class SemanticSearch:

    def __init__(self, connection: Neo4jConnection):

        self.driver = connection.driver
        self.database = connection.database

        self.model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2"
        )

    def create_vector_index(self):

        query = """
        CYPHER 25
        CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
        FOR (c:Chunk)
        ON c.embedding
        WITH [c.document_id]
        OPTIONS {
            indexConfig: {
                `vector.dimensions`: 384,
                `vector.similarity_function`: 'cosine'
            }
        }
        """

        with self.driver.session(database=self.database) as session:
            session.run(query)

        print("Vector index created successfully.")

    def embed_and_store_chunks(
        self,
        chunks,
        document_id: str,
        batch_size: int = 32
    ):

        total_chunks = len(chunks)

        for start in range(0, total_chunks, batch_size):

            batch = chunks[start:start + batch_size]

            texts = [
                chunk.page_content
                for chunk in batch
            ]

            # Convert chunk texts into numerical vectors
            embeddings = self.model.encode(
                texts,
                normalize_embeddings=True,
                show_progress_bar=False
            )

            records = []

            for offset, (chunk, embedding) in enumerate(
                zip(batch, embeddings)
            ):

                index = start + offset

                records.append({
                    "id": f"{document_id}_chunk_{index + 1}",
                    "document_id": document_id,
                    "text": chunk.page_content,
                    "page_number": chunk.metadata.get("page", 0) + 1,
                    "chunk_index": index,
                    "embedding": embedding.tolist()
                })

            query = """
            MATCH (d:Document {id: $document_id})

            UNWIND $records AS record

            MERGE (c:Chunk {id: record.id})

            SET c.text = record.text,
                c.document_id = record.document_id,
                c.page_number = record.page_number,
                c.chunk_index = record.chunk_index,
                c.embedding = record.embedding

            MERGE (d)-[:CONTAINS]->(c)
            """

            with self.driver.session(database=self.database) as session:

                session.run(
                    query,
                    document_id=document_id,
                    records=records
                )

            print(
                f"Embedded and stored "
                f"{min(start + batch_size, total_chunks)}"
                f"/{total_chunks} chunks"
            )

        print("All chunk embeddings stored successfully.")


    def search(
        self,
        question: str,
        top_k: int = 5,
        document_id: str = None
    ):

        query_embedding = self.model.encode(
            question,
            normalize_embeddings=True
        ).tolist()

        if document_id:

            query = """
            CYPHER 25
            MATCH (node:Chunk)
            SEARCH node IN (
                VECTOR INDEX chunk_embeddings
                FOR $embedding
                WHERE node.document_id = $document_id
                LIMIT $top_k
            ) SCORE AS score

            RETURN
                node.id AS chunk_id,
                node.document_id AS document_id,
                node.text AS text,
                node.page_number AS page_number,
                score

            ORDER BY score DESC
            """

            parameters = {
                "top_k": top_k,
                "embedding": query_embedding,
                "document_id": document_id
            }

        else:

            query = """
            CYPHER 25
            MATCH (node:Chunk)
            SEARCH node IN (
                VECTOR INDEX chunk_embeddings
                FOR $embedding
                LIMIT $top_k
            ) SCORE AS score

            RETURN
                node.id AS chunk_id,
                node.document_id AS document_id,
                node.text AS text,
                node.page_number AS page_number,
                score

            ORDER BY score DESC
            """

            parameters = {
                "top_k": top_k,
                "embedding": query_embedding
            }

        with self.driver.session(database=self.database) as session:

            result = session.run(query, **parameters)

            return [record.data() for record in result]


# node: Matching Chunk node.
# score: Similarity score. remember that the score is based on cosine similarity, so a higher score 
#        indicates a closer match to the query embedding.