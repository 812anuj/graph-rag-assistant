
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.cypher_generator import CypherGenerator
from src.retrieval.cypher_executor import CypherExecutor
from src.retrieval.answer_generator import AnswerGenerator


class GraphRAGRetriever:

    def __init__(self, connection, settings):

        self.cypher_generator = CypherGenerator(settings)

        self.cypher_executor = CypherExecutor(
            connection,
            settings,
            self.cypher_generator
        )

        self.hybrid_search = HybridSearch(connection)

        self.answer_generator = AnswerGenerator(settings)

    def retrieve(
        self,
        question: str,
        entity_name: str = None,
        top_k: int = 5,
        max_hops: int = 2,
        document_id: str = None
    ):

        # 1. Detect entity automatically if not provided
        if not entity_name:

            entity_name = self.hybrid_search.graph_search.detect_entity(
                question
            )

        # 2. Check whether an entity was detected
        if not entity_name:
            raise ValueError(
                "Could not identify an entity in your question. "
                "Try mentioning a known entity."
            )

        # 3. Generate and execute Cypher query
        cypher_query = self.cypher_generator.generate(question)

        cypher_results = self.cypher_executor.execute(cypher_query)

        # 4. Perform hybrid retrieval
        hybrid_results = self.hybrid_search.search(
            question=question,
            entity_name=entity_name,
            top_k=top_k,
            max_hops=max_hops,
            document_id=document_id
        )

        combined_chunks = hybrid_results["combined_chunks"]

        # 5. Generate grounded answer
        answer_results = self.answer_generator.generate_answer(
            question=question,
            retrieved_chunks=combined_chunks
        )

        # 6. Return all results
        return {
            "question": question,
            "entity_name": entity_name,
            "cypher_query": cypher_query,
            "cypher_results": cypher_results,
            "hybrid_results": hybrid_results,
            "combined_chunks": combined_chunks,
            "answer": answer_results["answer"],
            "sources": answer_results["sources"]
        }
