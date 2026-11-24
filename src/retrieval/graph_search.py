from src.graph.neo4j_connection import Neo4jConnection

class GraphSearch:

    def __init__(self, connection: Neo4jConnection):
        self.driver = connection.driver
        self.database = connection.database


    # --------------------------------------------------
    # 0. DETECT ENTITY FROM USER QUESTION
    # --------------------------------------------------

    def detect_entity(self, question: str):

        query = """
        MATCH (e:Entity)

        WHERE
            size(e.name) >= 5
            AND toLower($question) CONTAINS toLower(e.name)

        RETURN
            e.name AS entity,
            size(e.name) AS name_length

        ORDER BY name_length DESC

        LIMIT 1
        """

        with self.driver.session(database=self.database) as session:

            result = session.run(
                query,
                question=question
            )

            record = result.single()

            if record:
                return record["entity"]

            return None



    # --------------------------------------------------
    # 1. ONE-HOP GRAPH SEARCH
    # --------------------------------------------------

    def search(
        self,
        entity_name: str,
        document_id: str = None
    ):

        query = """
        MATCH (e:Entity)

        WHERE
            (
                $exact = true
                AND toLower(trim(e.name)) = toLower(trim($entity_name))
            )
            OR
            (
                $exact = false
                AND toLower(e.name) CONTAINS toLower($entity_name)
            )

        CALL (e) {
            OPTIONAL MATCH (e)-[r:RELATED_TO]-(related:Entity)

            WITH r, related
            WHERE related IS NOT NULL

            RETURN collect(DISTINCT {
                relationship: r.type,
                source_entity: startNode(r).name,
                target_entity: endNode(r).name,
                related_entity: related.name,
                description: r.description
            }) AS relationships
        }

        CALL (e) {
            OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(e)

            OPTIONAL MATCH (d:Document)-[:CONTAINS]->(c)

            WHERE
                c IS NOT NULL
                AND (
                    $document_id IS NULL
                    OR d.id = $document_id
                )

            RETURN collect(DISTINCT {
                chunk_id: c.id,
                text: c.text,
                page_number: c.page_number,
                document_id: d.id
            })[0..10] AS source_chunks
        }

        RETURN
            e.name AS entity,
            relationships,
            source_chunks

        LIMIT 10
        """

        with self.driver.session(database=self.database) as session:

            # First try exact matching
            result = session.run(
                query,
                entity_name=entity_name,
                exact=True,
                document_id=document_id
            )

            records = [record.data() for record in result]

            # If exact matching fails, try partial matching
            if not records:

                result = session.run(
                    query,
                    entity_name=entity_name,
                    exact=False,
                    document_id=document_id
                )

                records = [record.data() for record in result]

            return records

    # --------------------------------------------------
    # 2. MULTI-HOP GRAPH SEARCH
    # --------------------------------------------------
   
    def search_multi_hop(
        self,
        entity_name: str,
        max_hops: int = 2,
        document_id: str = None
    ):

        if not 1 <= max_hops <= 5:
            raise ValueError("max_hops must be between 1 and 5")

        query = """
        MATCH (start:Entity)
        WHERE
            (
                $exact = true
                AND toLower(trim(start.name)) = toLower(trim($entity_name))
            )
            OR
            (
                $exact = false
                AND toLower(start.name) CONTAINS toLower($entity_name)
            )

        MATCH path = (start)-[:RELATED_TO*1..5]->(related:Entity)
        WHERE length(path) <= $max_hops

        WITH
            start,
            related,
            path,
            relationships(path) AS rels,
            nodes(path) AS path_nodes

        UNWIND range(0, size(rels) - 1) AS i

        WITH
            start,
            related,
            path,
            i,
            rels[i] AS rel,
            path_nodes[i] AS source,
            path_nodes[i + 1] AS target

        // Find chunks that mention BOTH endpoints of this relationship.
        CALL (source, target) {
            OPTIONAL MATCH (c:Chunk)-[:MENTIONS]->(source)
            WHERE (c)-[:MENTIONS]->(target)

            OPTIONAL MATCH (d:Document)-[:CONTAINS]->(c)
            WHERE
                c IS NOT NULL
                AND (
                    $document_id IS NULL
                    OR d.id = $document_id
                )

            RETURN collect(
                DISTINCT CASE
                    WHEN c IS NOT NULL THEN {
                        chunk_id: c.id,
                        text: c.text,
                        page_number: c.page_number,
                        document_id: d.id
                    }
                END
            )[0..5] AS evidence_chunks
        }

        WITH
            start,
            related,
            path,
            i,
            rel,
            source,
            target,
            evidence_chunks

        ORDER BY i

        WITH
            start,
            related,
            path,
            collect({
                source_entity: source.name,
                relationship: rel.type,
                target_entity: target.name,
                description: rel.description,
                evidence_chunks: evidence_chunks
            }) AS relationship_path

        RETURN
            start.name AS starting_entity,
            related.name AS related_entity,
            length(path) AS hops,
            relationship_path

        ORDER BY hops
        LIMIT 50
        """

        with self.driver.session(database=self.database) as session:

            result = session.run(
                query,
                entity_name=entity_name,
                max_hops=max_hops,
                exact=True,
                document_id=document_id
            )

            records = [record.data() for record in result]

            if not records:
                result = session.run(
                    query,
                    entity_name=entity_name,
                    max_hops=max_hops,
                    exact=False,
                    document_id=document_id
                )

                records = [record.data() for record in result]

            return records
