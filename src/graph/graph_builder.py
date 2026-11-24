from .neo4j_connection import Neo4jConnection

class GraphBuilder:
    def __init__(self, connection: Neo4jConnection):
        self.driver = connection.driver
        self.database = connection.database

    def save_entity(self, entity):
        entity_id = entity.name.strip().lower()
        query = """
        MERGE (e:Entity {id: $entity_id})
        SET e.name = $name,
            e.entity_type = $entity_type,
            e.description = $description
        """

        with self.driver.session(database=self.database) as session:
            session.run(
                query,
                entity_id=entity_id,
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description
            )
        print(f"Entity saved: {entity.name}")

    def save_relationship(self, relationship):
        source_id = relationship.source.strip().lower()
        target_id = relationship.target.strip().lower()
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})

        MERGE (source)-[r:RELATED_TO {type: $relation_type}]->(target)

        SET r.description = $description
        """
        with self.driver.session(database=self.database) as session:
            session.run(
                query,
                source_id=source_id,
                target_id=target_id,
                relation_type=relationship.relation_type,
                description=relationship.description
            )

        print(
            f"Relationship saved: "
            f"{relationship.source} "
            f"--{relationship.relation_type}--> "
            f"{relationship.target}"
        )

    def save_document(self, document):

        query = """
        MERGE (d:Document {id: $document_id})

        SET d.name = $name,
            d.file_path = $file_path,
            d.total_pages = $total_pages
        """

        with self.driver.session(database=self.database) as session:

            session.run(
                query,
                document_id=document["id"],
                name=document["name"],
                file_path=document["file_path"],
                total_pages=document["total_pages"]
            )

        print(f"Document saved: {document['name']}")

    def save_chunk(self, chunk):
        query = """
        MERGE (c:Chunk {id: $chunk_id})

        SET c.text = $text,
            c.page_number = $page_number,
            c.chunk_index = $chunk_index
        """

        with self.driver.session(database=self.database) as session:

            session.run(
                query,
                chunk_id=chunk["id"],
                text=chunk["text"],
                page_number=chunk["page_number"],
                chunk_index=chunk["chunk_index"]
            )

        print(f"Chunk saved: {chunk['id']}")

    def connect_document_to_chunk(self, document_id, chunk_id):
        query = """
    MATCH (d:Document {id: $document_id})
    MATCH (c:Chunk {id: $chunk_id})

    MERGE (d)-[:CONTAINS]->(c)
    """
        with self.driver.session(database=self.database) as session:
            session.run(
                query,
                document_id=document_id,
                chunk_id=chunk_id
            )

        print(f"Connected document to chunk: {chunk_id}")

    def save_chunks(self, chunks, document_id):

        for index, chunk in enumerate(chunks):

            chunk_data = {
                "id": f"{document_id}_chunk_{index + 1}",
                "text": chunk.page_content,
                "page_number": chunk.metadata.get("page", 0) + 1,
                "chunk_index": index
            }

            self.save_chunk(chunk_data)

            self.connect_document_to_chunk(
                document_id=document_id,
                chunk_id=chunk_data["id"]
            )

        print(f"Total chunks saved: {len(chunks)}")

    def connect_chunk_to_entity(self, chunk_id, entity_id):
        query = """
        MATCH (c:Chunk {id: $chunk_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (c)-[r:MENTIONS]->(e)
        RETURN
            c.id AS chunk_id,
            e.id AS entity_id,
            type(r) AS relationship
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                chunk_id=chunk_id,
                entity_id=entity_id
            )

            record = result.single()

        if record:
            print(
                f"Connected: {record['chunk_id']} "
                f"--{record['relationship']}--> "
                f"{record['entity_id']}"
            )
        else:
            print(
                f"FAILED: Could not connect chunk {chunk_id} "
                f"to entity {entity_id}"
            )