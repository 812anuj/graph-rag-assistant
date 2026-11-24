## Knowledge Graph Visualization

### Objective
Visualize the entities and relationships extracted from the source document and stored in the Neo4j knowledge graph.

### Implementation
Neo4j Browser was used to visualize the knowledge graph through a Cypher query.

```cypher
MATCH (source:Entity)-[r:RELATED_TO]->(target:Entity)
RETURN source, r, target
LIMIT 50;
```

### Visualization Details
The graph displays:

- **Entity nodes:** Represent entities extracted from the source document.
- **RELATED_TO relationships:** Represent connections identified between entities.
- **Directed edges:** Show the direction of the extracted relationships.
- **Central entity:** The entity named "Interactive Platform..." has multiple connections to other entities.

### Result
Successfully visualized the extracted entities and their relationships using Neo4j Browser.

The visualization demonstrates how information extracted from an unstructured document is organized into a connected knowledge graph.

### Screenshot
` screenshots/knowledge_graph.png `

### Observation
The graph contains multiple connected entities and relationships. Some areas are dense, making individual relationships difficult to inspect. This visualization provides a useful overview of the knowledge graph structure.