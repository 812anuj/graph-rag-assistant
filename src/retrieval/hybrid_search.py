from src.retrieval.semantic_search import SemanticSearch
from src.retrieval.graph_search import GraphSearch

class HybridSearch:
    def __init__(self, connection):

        # Initialize existing retrieval systems
        self.semantic_search = SemanticSearch(connection)
        self.graph_search = GraphSearch(connection)

    def search(
        self,
        question: str,
        entity_name: str,
        top_k: int = 5,
        max_hops: int = 2,
        document_id: str = None
    ):

        # 1. Retrieve relevant chunks using vector search
        vector_results = self.semantic_search.search(
            question,
            top_k=top_k,
            document_id=document_id
        )

        # 2. Retrieve connected entities using graph search
        graph_results = self.graph_search.search_multi_hop(
            entity_name,
            max_hops=max_hops,
            document_id=document_id
        )

        # 3. Store all retrieved chunks without duplicates
        combined_chunks = {}

        # Add vector search results
        for chunk in vector_results:

            chunk_id = chunk["chunk_id"]

            combined_chunks[chunk_id] = {
                **chunk,
                "retrieval_sources": ["vector"],
                "graph_evidence": []
            }

        # Add graph search evidence
        for graph_result in graph_results:

            for relationship in graph_result["relationship_path"]:

                for chunk in relationship["evidence_chunks"]:

                    chunk_id = chunk["chunk_id"]

                    if chunk_id not in combined_chunks:

                        combined_chunks[chunk_id] = {
                            **chunk,
                            "score": None,
                            "retrieval_sources": [],
                            "graph_evidence": []
                        }

                    # Record graph as a retrieval source
                    if "graph" not in combined_chunks[chunk_id]["retrieval_sources"]:
                        combined_chunks[chunk_id]["retrieval_sources"].append(
                            "graph"
                        )

                    # Preserve the relationship supported by this chunk
                    evidence = {
                        "source_entity": relationship["source_entity"],
                        "relationship": relationship["relationship"],
                        "target_entity": relationship["target_entity"]
                    }

                    if evidence not in combined_chunks[chunk_id]["graph_evidence"]:
                        combined_chunks[chunk_id]["graph_evidence"].append(
                            evidence
                        )

        # 4. Return combined retrieval results
        return {
            "question": question,
            "entity_name": entity_name,
            "vector_results": vector_results,
            "graph_results": graph_results,
            "combined_chunks": list(combined_chunks.values())
        }
