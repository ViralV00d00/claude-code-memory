"""
Data models and schemas for Claude Code Memory Server.

This module defines the core data structures used throughout the memory system,
including memory types, relationships, and validation schemas.
"""

from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator


class MemoryType(str, Enum):
    """Types of memories that can be stored in the system."""
    
    TASK = "task"
    CODE_PATTERN = "code_pattern"
    PROBLEM = "problem"
    SOLUTION = "solution"
    PROJECT = "project"
    TECHNOLOGY = "technology"
    ERROR = "error"
    FIX = "fix"
    COMMAND = "command"
    FILE_CONTEXT = "file_context"
    WORKFLOW = "workflow"
    GENERAL = "general"


class RelationshipType(str, Enum):
    """Types of relationships between memories."""
    
    # Causal relationships
    CAUSES = "CAUSES"
    TRIGGERS = "TRIGGERS"
    LEADS_TO = "LEADS_TO"
    PREVENTS = "PREVENTS"
    BREAKS = "BREAKS"
    
    # Solution relationships
    SOLVES = "SOLVES"
    ADDRESSES = "ADDRESSES"
    ALTERNATIVE_TO = "ALTERNATIVE_TO"
    IMPROVES = "IMPROVES"
    REPLACES = "REPLACES"
    
    # Context relationships
    OCCURS_IN = "OCCURS_IN"
    APPLIES_TO = "APPLIES_TO"
    WORKS_WITH = "WORKS_WITH"
    REQUIRES = "REQUIRES"
    USED_IN = "USED_IN"
    
    # Learning relationships
    BUILDS_ON = "BUILDS_ON"
    CONTRADICTS = "CONTRADICTS"
    CONFIRMS = "CONFIRMS"
    GENERALIZES = "GENERALIZES"
    SPECIALIZES = "SPECIALIZES"
    
    # Similarity relationships
    SIMILAR_TO = "SIMILAR_TO"
    VARIANT_OF = "VARIANT_OF"
    RELATED_TO = "RELATED_TO"
    ANALOGY_TO = "ANALOGY_TO"
    OPPOSITE_OF = "OPPOSITE_OF"
    
    # Workflow relationships
    FOLLOWS = "FOLLOWS"
    DEPENDS_ON = "DEPENDS_ON"
    ENABLES = "ENABLES"
    BLOCKS = "BLOCKS"
    PARALLEL_TO = "PARALLEL_TO"
    
    # Quality relationships
    EFFECTIVE_FOR = "EFFECTIVE_FOR"
    INEFFECTIVE_FOR = "INEFFECTIVE_FOR"
    PREFERRED_OVER = "PREFERRED_OVER"
    DEPRECATED_BY = "DEPRECATED_BY"
    VALIDATED_BY = "VALIDATED_BY"


class MemoryContext(BaseModel):
    """Context information for a memory."""
    
    project_path: Optional[str] = None
    files_involved: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    technologies: List[str] = Field(default_factory=list)
    git_commit: Optional[str] = None
    git_branch: Optional[str] = None
    working_directory: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    additional_metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Memory(BaseModel):
    """Core memory data structure."""
    
    id: Optional[str] = None
    type: MemoryType
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = Field(None, max_length=500)
    tags: List[str] = Field(default_factory=list)
    context: Optional[MemoryContext] = None
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    usage_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed: Optional[datetime] = None
    
    @validator('tags')
    def validate_tags(cls, v):
        """Ensure tags are lowercase and non-empty."""
        return [tag.lower().strip() for tag in v if tag.strip()]
    
    @validator('title', 'content')
    def validate_text_fields(cls, v):
        """Ensure text fields are properly formatted."""
        return v.strip()

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RelationshipProperties(BaseModel):
    """Properties for relationships between memories."""
    
    strength: float = Field(default=0.5, ge=0.0, le=1.0)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    context: Optional[str] = None
    evidence_count: int = Field(default=1, ge=0)
    success_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_validated: datetime = Field(default_factory=datetime.utcnow)
    validation_count: int = Field(default=0, ge=0)
    counter_evidence_count: int = Field(default=0, ge=0)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Relationship(BaseModel):
    """Relationship between two memories."""
    
    id: Optional[str] = None
    from_memory_id: str
    to_memory_id: str
    type: RelationshipType
    properties: RelationshipProperties = Field(default_factory=RelationshipProperties)
    description: Optional[str] = None
    bidirectional: bool = Field(default=False)
    
    @validator('from_memory_id', 'to_memory_id')
    def validate_memory_ids(cls, v):
        """Ensure memory IDs are non-empty."""
        if not v or not v.strip():
            raise ValueError('Memory ID cannot be empty')
        return v.strip()


class MemoryNode(BaseModel):
    """Neo4j node representation of a memory."""
    
    memory: Memory
    node_id: Optional[int] = None  # Neo4j internal node ID
    labels: List[str] = Field(default_factory=list)
    
    def to_neo4j_properties(self) -> Dict[str, Any]:
        """Convert memory to Neo4j node properties."""
        props = {
            'id': self.memory.id,
            'type': self.memory.type.value,
            'title': self.memory.title,
            'content': self.memory.content,
            'tags': self.memory.tags,
            'importance': self.memory.importance,
            'confidence': self.memory.confidence,
            'usage_count': self.memory.usage_count,
            'created_at': self.memory.created_at.isoformat(),
            'updated_at': self.memory.updated_at.isoformat(),
        }
        
        # Add optional fields if present
        if self.memory.summary:
            props['summary'] = self.memory.summary
        if self.memory.effectiveness is not None:
            props['effectiveness'] = self.memory.effectiveness
        if self.memory.last_accessed:
            props['last_accessed'] = self.memory.last_accessed.isoformat()
        
        # Add context information if present
        if self.memory.context:
            context_data = self.memory.context.dict()
            for key, value in context_data.items():
                if value is not None:
                    if isinstance(value, datetime):
                        props[f'context_{key}'] = value.isoformat()
                    elif isinstance(value, (list, dict)):
                        props[f'context_{key}'] = str(value) if value else None
                    else:
                        props[f'context_{key}'] = value
        
        return props


class SearchQuery(BaseModel):
    """Search query parameters for memory retrieval."""
    
    query: Optional[str] = None
    memory_types: List[MemoryType] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    project_path: Optional[str] = None
    languages: List[str] = Field(default_factory=list)
    frameworks: List[str] = Field(default_factory=list)
    min_importance: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    min_effectiveness: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    limit: int = Field(default=20, ge=1, le=100)
    include_relationships: bool = Field(default=True)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MemoryGraph(BaseModel):
    """Graph representation of memories and their relationships."""
    
    memories: List[Memory]
    relationships: List[Relationship]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Memory]:
        """Get a memory by its ID."""
        return next((m for m in self.memories if m.id == memory_id), None)
    
    def get_relationships_for_memory(self, memory_id: str) -> List[Relationship]:
        """Get all relationships involving a specific memory."""
        return [
            r for r in self.relationships 
            if r.from_memory_id == memory_id or r.to_memory_id == memory_id
        ]


class AnalysisResult(BaseModel):
    """Result of memory or relationship analysis."""
    
    analysis_type: str
    results: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }