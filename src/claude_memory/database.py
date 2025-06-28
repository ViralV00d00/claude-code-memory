"""
Neo4j database connection and management for Claude Code Memory Server.

This module handles all database operations, connection management, and provides
a high-level interface for interacting with the Neo4j graph database.
"""

import os
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import contextmanager
import uuid
from datetime import datetime

from neo4j import GraphDatabase, Driver, Transaction, Session
from neo4j.exceptions import ServiceUnavailable, AuthError, Neo4jError

from .models import (
    Memory, MemoryType, MemoryNode, Relationship, RelationshipType,
    RelationshipProperties, SearchQuery, MemoryGraph, MemoryContext
)


logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Manages Neo4j database connection and operations."""
    
    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None,
        database: str = "neo4j"
    ):
        """Initialize Neo4j connection.
        
        Args:
            uri: Neo4j database URI (defaults to NEO4J_URI env var or bolt://localhost:7687)
            user: Database username (defaults to NEO4J_USER env var or 'neo4j')
            password: Database password (defaults to NEO4J_PASSWORD env var)
            database: Database name (defaults to 'neo4j')
        """
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database
        self.driver: Optional[Driver] = None
        
        if not self.password:
            raise ValueError("Neo4j password must be provided via parameter or NEO4J_PASSWORD env var")
    
    def connect(self) -> None:
        """Establish connection to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=30 * 60,  # 30 minutes
                max_connection_pool_size=50,
                connection_acquisition_timeout=30.0
            )
            
            # Verify connectivity
            self.driver.verify_connectivity()
            logger.info(f"Successfully connected to Neo4j at {self.uri}")
            
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except AuthError as e:
            logger.error(f"Authentication failed for Neo4j: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Neo4j: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            self.driver = None
            logger.info("Neo4j connection closed")
    
    @contextmanager
    def session(self, database: str = None):
        """Context manager for Neo4j session."""
        if not self.driver:
            raise RuntimeError("Not connected to Neo4j. Call connect() first.")
        
        session = self.driver.session(database=database or self.database)
        try:
            yield session
        finally:
            session.close()
    
    def execute_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        with self.session(database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def execute_write_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """Execute a write query in a transaction."""
        with self.session(database) as session:
            return session.write_transaction(self._run_query, query, parameters or {})
    
    def execute_read_query(
        self,
        query: str,
        parameters: Dict[str, Any] = None,
        database: str = None
    ) -> List[Dict[str, Any]]:
        """Execute a read query in a transaction."""
        with self.session(database) as session:
            return session.read_transaction(self._run_query, query, parameters or {})
    
    @staticmethod
    def _run_query(tx: Transaction, query: str, parameters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Helper method to run a query within a transaction."""
        result = tx.run(query, parameters)
        return [record.data() for record in result]


class MemoryDatabase:
    """High-level interface for memory database operations."""
    
    def __init__(self, connection: Neo4jConnection):
        """Initialize with a Neo4j connection."""
        self.connection = connection
    
    async def initialize_schema(self) -> None:
        """Create database schema, constraints, and indexes."""
        logger.info("Initializing Neo4j schema for Claude Memory...")
        
        # Create constraints
        constraints = [
            "CREATE CONSTRAINT memory_id_unique IF NOT EXISTS FOR (m:Memory) REQUIRE m.id IS UNIQUE",
            "CREATE CONSTRAINT relationship_id_unique IF NOT EXISTS FOR (r:RELATIONSHIP) REQUIRE r.id IS UNIQUE",
        ]
        
        # Create indexes for performance
        indexes = [
            "CREATE INDEX memory_type_index IF NOT EXISTS FOR (m:Memory) ON (m.type)",
            "CREATE INDEX memory_created_at_index IF NOT EXISTS FOR (m:Memory) ON (m.created_at)",
            "CREATE INDEX memory_tags_index IF NOT EXISTS FOR (m:Memory) ON (m.tags)",
            "CREATE FULLTEXT INDEX memory_content_index IF NOT EXISTS FOR (m:Memory) ON EACH [m.title, m.content, m.summary]",
            "CREATE INDEX memory_importance_index IF NOT EXISTS FOR (m:Memory) ON (m.importance)",
            "CREATE INDEX memory_confidence_index IF NOT EXISTS FOR (m:Memory) ON (m.confidence)",
            "CREATE INDEX memory_project_path_index IF NOT EXISTS FOR (m:Memory) ON (m.context_project_path)",
        ]
        
        # Execute schema creation
        for constraint in constraints:
            try:
                self.connection.execute_write_query(constraint)
                logger.debug(f"Created constraint: {constraint}")
            except Neo4jError as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create constraint: {e}")
        
        for index in indexes:
            try:
                self.connection.execute_write_query(index)
                logger.debug(f"Created index: {index}")
            except Neo4jError as e:
                if "already exists" not in str(e).lower():
                    logger.warning(f"Failed to create index: {e}")
        
        logger.info("Schema initialization completed")
    
    def store_memory(self, memory: Memory) -> str:
        """Store a memory in the database and return its ID."""
        if not memory.id:
            memory.id = str(uuid.uuid4())
        
        memory.updated_at = datetime.utcnow()
        
        # Convert memory to Neo4j properties
        memory_node = MemoryNode(memory=memory)
        properties = memory_node.to_neo4j_properties()
        
        query = """
        MERGE (m:Memory {id: $id})
        SET m += $properties
        RETURN m.id as id
        """
        
        result = self.connection.execute_write_query(
            query,
            {"id": memory.id, "properties": properties}
        )
        
        if result:
            logger.info(f"Stored memory: {memory.id} ({memory.type})")
            return result[0]["id"]
        else:
            raise RuntimeError(f"Failed to store memory: {memory.id}")
    
    def get_memory(self, memory_id: str, include_relationships: bool = True) -> Optional[Memory]:
        """Retrieve a memory by ID."""
        query = """
        MATCH (m:Memory {id: $memory_id})
        RETURN m
        """
        
        result = self.connection.execute_read_query(query, {"memory_id": memory_id})
        
        if not result:
            return None
        
        memory_data = result[0]["m"]
        return self._neo4j_to_memory(memory_data)
    
    def search_memories(self, search_query: SearchQuery) -> List[Memory]:
        """Search for memories based on query parameters."""
        conditions = []
        parameters = {}
        
        # Build WHERE conditions based on search parameters
        if search_query.query:
            conditions.append("(m.title CONTAINS $query OR m.content CONTAINS $query OR m.summary CONTAINS $query)")
            parameters["query"] = search_query.query
        
        if search_query.memory_types:
            conditions.append("m.type IN $memory_types")
            parameters["memory_types"] = [t.value for t in search_query.memory_types]
        
        if search_query.tags:
            conditions.append("ANY(tag IN $tags WHERE tag IN m.tags)")
            parameters["tags"] = search_query.tags
        
        if search_query.project_path:
            conditions.append("m.context_project_path = $project_path")
            parameters["project_path"] = search_query.project_path
        
        if search_query.min_importance is not None:
            conditions.append("m.importance >= $min_importance")
            parameters["min_importance"] = search_query.min_importance
        
        if search_query.min_confidence is not None:
            conditions.append("m.confidence >= $min_confidence")
            parameters["min_confidence"] = search_query.min_confidence
        
        if search_query.created_after:
            conditions.append("datetime(m.created_at) >= datetime($created_after)")
            parameters["created_after"] = search_query.created_after.isoformat()
        
        if search_query.created_before:
            conditions.append("datetime(m.created_at) <= datetime($created_before)")
            parameters["created_before"] = search_query.created_before.isoformat()
        
        # Build the complete query
        where_clause = " AND ".join(conditions) if conditions else "true"
        
        query = f"""
        MATCH (m:Memory)
        WHERE {where_clause}
        RETURN m
        ORDER BY m.importance DESC, m.created_at DESC
        LIMIT $limit
        """
        
        parameters["limit"] = search_query.limit
        
        result = self.connection.execute_read_query(query, parameters)
        
        memories = []
        for record in result:
            memory = self._neo4j_to_memory(record["m"])
            if memory:
                memories.append(memory)
        
        logger.info(f"Found {len(memories)} memories for search query")
        return memories
    
    def update_memory(self, memory: Memory) -> bool:
        """Update an existing memory."""
        if not memory.id:
            raise ValueError("Memory must have an ID to update")
        
        memory.updated_at = datetime.utcnow()
        
        # Convert memory to Neo4j properties
        memory_node = MemoryNode(memory=memory)
        properties = memory_node.to_neo4j_properties()
        
        query = """
        MATCH (m:Memory {id: $id})
        SET m += $properties
        RETURN m.id as id
        """
        
        result = self.connection.execute_write_query(
            query,
            {"id": memory.id, "properties": properties}
        )
        
        success = len(result) > 0
        if success:
            logger.info(f"Updated memory: {memory.id}")
        
        return success
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory and all its relationships."""
        query = """
        MATCH (m:Memory {id: $memory_id})
        DETACH DELETE m
        RETURN COUNT(m) as deleted_count
        """
        
        result = self.connection.execute_write_query(query, {"memory_id": memory_id})
        
        success = result and result[0]["deleted_count"] > 0
        if success:
            logger.info(f"Deleted memory: {memory_id}")
        
        return success
    
    def create_relationship(
        self,
        from_memory_id: str,
        to_memory_id: str,
        relationship_type: RelationshipType,
        properties: RelationshipProperties = None
    ) -> str:
        """Create a relationship between two memories."""
        relationship_id = str(uuid.uuid4())
        
        if properties is None:
            properties = RelationshipProperties()
        
        # Convert properties to dict for Neo4j
        props_dict = properties.dict()
        props_dict['id'] = relationship_id
        props_dict['created_at'] = props_dict['created_at'].isoformat()
        props_dict['last_validated'] = props_dict['last_validated'].isoformat()
        
        query = f"""
        MATCH (from:Memory {{id: $from_id}})
        MATCH (to:Memory {{id: $to_id}})
        CREATE (from)-[r:{relationship_type.value} $properties]->(to)
        RETURN r.id as id
        """
        
        result = self.connection.execute_write_query(
            query,
            {
                "from_id": from_memory_id,
                "to_id": to_memory_id,
                "properties": props_dict
            }
        )
        
        if result:
            logger.info(f"Created relationship: {relationship_type.value} between {from_memory_id} and {to_memory_id}")
            return result[0]["id"]
        else:
            raise RuntimeError(f"Failed to create relationship between {from_memory_id} and {to_memory_id}")
    
    def get_related_memories(
        self,
        memory_id: str,
        relationship_types: List[RelationshipType] = None,
        max_depth: int = 2
    ) -> List[Tuple[Memory, Relationship]]:
        """Get memories related to a specific memory."""
        # Build relationship type filter
        rel_filter = ""
        if relationship_types:
            rel_types = "|".join([rt.value for rt in relationship_types])
            rel_filter = f":{rel_types}"
        
        query = f"""
        MATCH (start:Memory {{id: $memory_id}})
        MATCH (start)-[r{rel_filter}*1..{max_depth}]-(related:Memory)
        WHERE related.id <> start.id
        RETURN DISTINCT related, r[0] as relationship
        ORDER BY r[0].strength DESC, related.importance DESC
        LIMIT 20
        """
        
        result = self.connection.execute_read_query(query, {"memory_id": memory_id})
        
        related_memories = []
        for record in result:
            memory = self._neo4j_to_memory(record["related"])
            if memory:
                # Note: Simplified relationship extraction - in production you'd want more detailed relationship info
                rel_data = record.get("relationship", {})
                relationship = Relationship(
                    from_memory_id=memory_id,
                    to_memory_id=memory.id,
                    type=RelationshipType(rel_data.get("type", "RELATED_TO")),
                    properties=RelationshipProperties(
                        strength=rel_data.get("strength", 0.5),
                        confidence=rel_data.get("confidence", 0.8)
                    )
                )
                related_memories.append((memory, relationship))
        
        logger.info(f"Found {len(related_memories)} related memories for {memory_id}")
        return related_memories
    
    def _neo4j_to_memory(self, node_data: Dict[str, Any]) -> Optional[Memory]:
        """Convert Neo4j node data to Memory object."""
        try:
            # Extract basic memory fields
            memory_data = {
                "id": node_data.get("id"),
                "type": MemoryType(node_data.get("type")),
                "title": node_data.get("title"),
                "content": node_data.get("content"),
                "summary": node_data.get("summary"),
                "tags": node_data.get("tags", []),
                "importance": node_data.get("importance", 0.5),
                "confidence": node_data.get("confidence", 0.8),
                "effectiveness": node_data.get("effectiveness"),
                "usage_count": node_data.get("usage_count", 0),
                "created_at": datetime.fromisoformat(node_data.get("created_at")),
                "updated_at": datetime.fromisoformat(node_data.get("updated_at")),
            }
            
            # Handle optional last_accessed field
            if node_data.get("last_accessed"):
                memory_data["last_accessed"] = datetime.fromisoformat(node_data["last_accessed"])
            
            # Extract context information
            context_data = {}
            for key, value in node_data.items():
                if key.startswith("context_") and value is not None:
                    context_key = key[8:]  # Remove "context_" prefix
                    context_data[context_key] = value
            
            if context_data:
                # Handle timestamp fields in context
                for time_field in ["timestamp"]:
                    if time_field in context_data:
                        context_data[time_field] = datetime.fromisoformat(context_data[time_field])
                
                memory_data["context"] = MemoryContext(**context_data)
            
            return Memory(**memory_data)
            
        except Exception as e:
            logger.error(f"Failed to convert Neo4j node to Memory: {e}")
            return None
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """Get database statistics and metrics."""
        queries = {
            "total_memories": "MATCH (m:Memory) RETURN COUNT(m) as count",
            "memories_by_type": """
                MATCH (m:Memory)
                RETURN m.type as type, COUNT(m) as count
                ORDER BY count DESC
            """,
            "total_relationships": "MATCH ()-[r]->() RETURN COUNT(r) as count",
            "avg_importance": "MATCH (m:Memory) RETURN AVG(m.importance) as avg_importance",
            "avg_confidence": "MATCH (m:Memory) RETURN AVG(m.confidence) as avg_confidence",
        }
        
        stats = {}
        for stat_name, query in queries.items():
            try:
                result = self.connection.execute_read_query(query)
                if stat_name == "memories_by_type":
                    stats[stat_name] = {record["type"]: record["count"] for record in result}
                else:
                    stats[stat_name] = result[0] if result else None
            except Exception as e:
                logger.error(f"Failed to get statistic {stat_name}: {e}")
                stats[stat_name] = None
        
        return stats