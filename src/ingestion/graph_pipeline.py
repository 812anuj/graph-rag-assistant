from langchain_core.documents import Document

from src.config.settings import Settings
from src.extraction.entity_extractor import EntityExtractor
from src.graph.neo4j_connection import Neo4jConnection
from src.graph.graph_builder import GraphBuilder


class GraphPipeline:

    def __init__(
        self,
        settings: Settings,
        connection: Neo4jConnection
    ):

        self.extractor = EntityExtractor(settings)
        self.graph_builder = GraphBuilder(connection)

        # Number of chunks sent in one API request
        self.batch_size = 5

    # ----------------------------------
    # SAVE ONE CHUNK'S EXTRACTION
    # ----------------------------------

    def save_extraction(
        self,
        extraction_result,
        chunk_id: str
    ):

        # 1. Save entities and connect them to their chunk
        for entity in extraction_result.entities:

            self.graph_builder.save_entity(entity)

            self.graph_builder.connect_chunk_to_entity(
                chunk_id=chunk_id,
                entity_id=entity.name.strip().lower()
            )

        # 2. Save relationships after entities
        for relationship in extraction_result.relationships:

            self.graph_builder.save_relationship(relationship)

    # ----------------------------------
    # SINGLE CHUNK PROCESSING
    # ----------------------------------

    def process_chunk(
        self,
        chunk: Document,
        chunk_id: str
    ):

        extraction_result = self.extractor.extract(
            chunk.page_content
        )

        self.save_extraction(
            extraction_result,
            chunk_id
        )

        return {
            "metadata": chunk.metadata,
            "extraction": extraction_result
        }

    # ----------------------------------
    # BATCH DOCUMENT PROCESSING
    # ----------------------------------

    def process_documents(
        self,
        chunks: list[Document],
        document_id: str
    ):

        # 1. Save chunks and connect them to the document
        self.graph_builder.save_chunks(
            chunks,
            document_id
        )

        total_chunks = len(chunks)

        successful_chunks = 0
        failed_chunks = 0

        # 2. Divide chunks into batches of five
        for start in range(0, total_chunks, self.batch_size):

            batch = chunks[start:start + self.batch_size]

            batch_number = (start // self.batch_size) + 1

            print(
                f"\nProcessing batch {batch_number} "
                f"({len(batch)} chunks)"
            )

            # Generate the correct ID for every chunk
            batch_inputs = []

            for index, chunk in enumerate(
                batch,
                start=start + 1
            ):

                chunk_id = f"{document_id}_chunk_{index}"

                batch_inputs.append({
                    "chunk_id": chunk_id,
                    "text": chunk.page_content
                })

            # 3. Send all five chunks in one Groq request
            try:

                batch_result = self.extractor.extract_batch(
                    batch_inputs
                )

            except Exception as error:

                failed_chunks += len(batch)

                print(f"Batch {batch_number} failed.")
                print(f"Error: {error}")

                # Continue with the next batch
                continue

            # 4. Match each extraction to its original chunk
            extraction_map = {
                item.chunk_id: item
                for item in batch_result.results
            }

            # 5. Save each chunk's extracted information
            for item in batch_inputs:

                chunk_id = item["chunk_id"]

                try:

                    extraction_result = extraction_map[chunk_id]

                    self.save_extraction(
                        extraction_result,
                        chunk_id
                    )

                    successful_chunks += 1

                except Exception as error:

                    failed_chunks += 1

                    print(f"Failed to save {chunk_id}")
                    print(f"Error: {error}")

        # 6. Display summary
        print("\n========== BATCH INGESTION SUMMARY ==========")

        print(f"Total chunks: {total_chunks}")
        print(f"Batch size: {self.batch_size}")
        print(
            f"Total batches: "
            f"{(total_chunks + self.batch_size - 1) // self.batch_size}"
        )
        print(f"Successful chunks: {successful_chunks}")
        print(f"Failed chunks: {failed_chunks}")
