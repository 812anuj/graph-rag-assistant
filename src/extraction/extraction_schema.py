from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str = Field(description="Name of the entity")
    entity_type: str = Field(
        description="Type of entity, such as Person, Organization, Location, or Technology"
    )
    description: str = Field(
        description="Short description of the entity"
    )


class Relationship(BaseModel):
    source: str = Field(description="Name of the source entity")
    target: str = Field(description="Name of the target entity")
    relation_type: str = Field(
        description="Type of relationship, such as CREATED, WORKS_AT, or LOCATED_IN"
    )
    description: str = Field(
        description="Short explanation of the relationship"
    )


class ExtractionResult(BaseModel):
    entities: list[Entity] = Field(
        description="List of entities extracted from the text"
    )
    relationships: list[Relationship] = Field(
        description="List of relationships between entities"
    )


# Result extracted from one chunk inside a batch
class ChunkExtractionResult(BaseModel):
    chunk_id: str
    entities: list[Entity]
    relationships: list[Relationship]


# Complete result returned for a batch of chunks
class BatchExtractionResult(BaseModel):
    results: list[ChunkExtractionResult]
