import json

from groq import Groq

from src.config.settings import Settings
from src.extraction.extraction_schema import (
    ExtractionResult,
    BatchExtractionResult
)

class EntityExtractor:
    def __init__(self, settings: Settings):

        self.client = Groq(
            api_key=settings.groq_api_key
        )

        self.model = "openai/gpt-oss-120b"

    # ----------------------------------
    # SINGLE CHUNK EXTRACTION
    # ----------------------------------

    def extract(self, text: str) -> ExtractionResult:

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": """
You are an information extraction assistant.

Extract entities and relationships from the provided text.

Rules:

1. Extract only information explicitly supported by the text.
2. Do not invent facts.
3. Every relationship source and target must match
   the name of an extracted entity.
4. If no entities are found, return an empty entities list.
5. If no relationships are found, return an empty relationships list.
"""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "entity_extraction",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "entity_type": {"type": "string"},
                                        "description": {"type": "string"}
                                    },
                                    "required": [
                                        "name",
                                        "entity_type",
                                        "description"
                                    ],
                                    "additionalProperties": False
                                }
                            },
                            "relationships": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "source": {"type": "string"},
                                        "target": {"type": "string"},
                                        "relation_type": {"type": "string"},
                                        "description": {"type": "string"}
                                    },
                                    "required": [
                                        "source",
                                        "target",
                                        "relation_type",
                                        "description"
                                    ],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": [
                            "entities",
                            "relationships"
                        ],
                        "additionalProperties": False
                    }
                }
            },

            temperature=0
        )

        response_text = response.choices[0].message.content

        extracted_data = json.loads(response_text)

        result = ExtractionResult.model_validate(extracted_data)

        return result

    # ----------------------------------
    # BATCH EXTRACTION
    # ----------------------------------

    def extract_batch(
        self,
        chunks: list[dict[str, str]]
    ) -> BatchExtractionResult:

        if not 1 <= len(chunks) <= 5:
            raise ValueError(
                "Batch must contain between 1 and 5 chunks."
            )

        chunk_ids = [chunk["chunk_id"] for chunk in chunks]

        if len(chunk_ids) != len(set(chunk_ids)):
            raise ValueError("Duplicate chunk IDs found in batch.")

        # Convert the chunks into JSON for Groq
        chunks_json = json.dumps(
            chunks,
            ensure_ascii=False
        )

        response = self.client.chat.completions.create(

            model=self.model,

            messages=[
                {
                    "role": "system",
                    "content": """
You are an information extraction assistant.

You will receive multiple document chunks.

Extract entities and relationships separately for EACH chunk.

IMPORTANT RULES:

1. Process every chunk independently.
2. Never mix information from different chunks.
3. Return the exact chunk_id provided in the input.
4. Extract only information explicitly supported by that chunk.
5. Do not invent facts.
6. Every relationship source and target must match
   the name of an entity extracted from the SAME chunk.
7. If a chunk has no entities, return an empty entities list.
8. If a chunk has no relationships, return an empty relationships list.
9. Return exactly one result for every input chunk.
10. Do not omit any chunk.
"""
                },
                {
                    "role": "user",
                    "content": chunks_json
                }
            ],

            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "batch_entity_extraction",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "results": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "chunk_id": {
                                            "type": "string"
                                        },
                                        "entities": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "entity_type": {
                                                        "type": "string"
                                                    },
                                                    "description": {
                                                        "type": "string"
                                                    }
                                                },
                                                "required": [
                                                    "name",
                                                    "entity_type",
                                                    "description"
                                                ],
                                                "additionalProperties": False
                                            }
                                        },
                                        "relationships": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "source": {
                                                        "type": "string"
                                                    },
                                                    "target": {
                                                        "type": "string"
                                                    },
                                                    "relation_type": {
                                                        "type": "string"
                                                    },
                                                    "description": {
                                                        "type": "string"
                                                    }
                                                },
                                                "required": [
                                                    "source",
                                                    "target",
                                                    "relation_type",
                                                    "description"
                                                ],
                                                "additionalProperties": False
                                            }
                                        }
                                    },
                                    "required": [
                                        "chunk_id",
                                        "entities",
                                        "relationships"
                                    ],
                                    "additionalProperties": False
                                }
                            }
                        },
                        "required": [
                            "results"
                        ],
                        "additionalProperties": False
                    }
                }
            },

            temperature=0
        )

        # Get the AI-generated JSON
        response_text = response.choices[0].message.content

        extracted_data = json.loads(response_text)

        # Validate using Pydantic
        result = BatchExtractionResult.model_validate(
            extracted_data
        )

        # Verify that Groq returned exactly the requested chunks
        returned_ids = [
            item.chunk_id for item in result.results
        ]

        if (
            len(returned_ids) != len(chunk_ids)
            or set(returned_ids) != set(chunk_ids)
        ):
            raise ValueError(
                "Batch response has missing, extra, or duplicate chunk IDs."
            )

        return result
