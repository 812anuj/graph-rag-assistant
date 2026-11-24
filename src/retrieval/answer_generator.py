from groq import Groq
from src.config.settings import Settings

class AnswerGenerator:
    def __init__(self, settings: Settings):
        self.client = Groq(
            api_key=settings.groq_api_key
        )
        self.model = "openai/gpt-oss-120b"

    def generate_answer(self, question: str, retrieved_chunks: list):

        # Remove synthetic test chunks.
        # We only want evidence from the original PDF.
        valid_chunks = [
            chunk
            for chunk in retrieved_chunks
            if not chunk["chunk_id"].startswith("batch_test_")
        ]

        # If no real evidence is available, do not call the LLM.
        if not valid_chunks:
            return {
                "answer": "I could not find sufficient supporting information in the source document.",
                "sources": []
            }

        # Prepare source passages for the LLM.
        context_parts = []

        for chunk in valid_chunks:

            chunk_context = f"""
            Chunk ID: {chunk['chunk_id']}
            Page Number: {chunk.get('page_number')}
            Passage:
            {chunk['text']}
            """

            context_parts.append(chunk_context)

        context = "\n\n".join(context_parts)

        # Prepare graph relationship information.
        graph_context = []

        for chunk in valid_chunks:

            for evidence in chunk.get("graph_evidence", []):

                relationship = (
                    f"{evidence['source_entity']} "
                    f"-[{evidence['relationship']}]-> "
                    f"{evidence['target_entity']}"
                )

                if relationship not in graph_context:
                    graph_context.append(relationship)

        graph_information = "\n".join(graph_context)

        # Instructions for the LLM.
       
        system_prompt = """
        You are a question-answering assistant for a Graph RAG system.

        Answer the user's question using only the provided source passages.

        Rules:
        1. Do not invent facts or use outside knowledge.
        2. If the passages do not contain enough information,
        clearly say that the evidence is insufficient.
        3. Use graph relationships as additional context,
        not as proof of a fact.
        4. Only state a graph relationship as a fact when
        the source passages support it.
        5. Do not include citations, page numbers, chunk IDs,
        or source references in your answer.
        6. Write a clear, natural, and understandable answer.
        """

        user_prompt = f"""
        QUESTION:
        {question}

        SOURCE PASSAGES:
        {context}

        GRAPH RELATIONSHIP CONTEXT:
        {graph_information}

        Provide a grounded answer with citations.
        """

        # Send the question and evidence to Groq.
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0
        )

        answer = response.choices[0].message.content

        # Return the answer and the available source references.
        sources = [
        {
            "chunk_id": chunk["chunk_id"],
            "page_number": chunk.get("page_number"),
            "text": chunk["text"],
            "score": chunk.get("score"),
            "retrieval_sources": chunk.get("retrieval_sources", []),
            "graph_evidence": chunk.get("graph_evidence", [])
        }
        for chunk in valid_chunks
    ]

        return {
            "answer": answer,
            "sources": sources
        }
