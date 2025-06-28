# Claude Code Memory Server

A Neo4j-based Model Context Protocol (MCP) server that provides intelligent memory capabilities for Claude Code, enabling persistent knowledge tracking, relationship mapping, and contextual development assistance.

## Overview

This MCP server creates a sophisticated memory system that tracks Claude Code's activities, decisions, and learned patterns to provide contextual memory across sessions and projects. It uses Neo4j as a graph database to capture and analyze complex relationships between development concepts, solutions, and workflows.

## Features

### Core Memory Operations
- **Persistent Memory Storage** - Store development tasks, solutions, and patterns
- **Intelligent Search** - Find relevant memories by context, content, or relationships
- **Relationship Mapping** - Track how different concepts, files, and solutions relate
- **Context Awareness** - Project-specific and technology-specific memory retrieval

### Advanced Intelligence
- **Pattern Recognition** - Automatically identify reusable development patterns
- **Solution Effectiveness** - Track and learn from successful approaches
- **Workflow Memory** - Remember and suggest optimal development sequences
- **Error Prevention** - Learn from past mistakes to prevent similar issues

### Development Integration
- **Task Execution Tracking** - Monitor what Claude Code does and how
- **Code Pattern Analysis** - Identify and store successful code patterns
- **Project Context Memory** - Understand codebase conventions and dependencies
- **Collaborative Learning** - Share knowledge across development sessions

## Architecture

### Memory Types
- **Task** - Development tasks and their execution patterns
- **CodePattern** - Reusable code solutions and architectural decisions
- **Problem** - Issues encountered and their context
- **Solution** - How problems were resolved and their effectiveness
- **Project** - Codebase context and project-specific knowledge
- **Technology** - Framework, language, and tool-specific knowledge

### Relationship Types
The system tracks seven categories of relationships:

1. **Causal** - `CAUSES`, `TRIGGERS`, `LEADS_TO`, `PREVENTS`, `BREAKS`
2. **Solution** - `SOLVES`, `ADDRESSES`, `ALTERNATIVE_TO`, `IMPROVES`, `REPLACES`
3. **Context** - `OCCURS_IN`, `APPLIES_TO`, `WORKS_WITH`, `REQUIRES`, `USED_IN`
4. **Learning** - `BUILDS_ON`, `CONTRADICTS`, `CONFIRMS`, `GENERALIZES`, `SPECIALIZES`
5. **Similarity** - `SIMILAR_TO`, `VARIANT_OF`, `RELATED_TO`, `ANALOGY_TO`, `OPPOSITE_OF`
6. **Workflow** - `FOLLOWS`, `DEPENDS_ON`, `ENABLES`, `BLOCKS`, `PARALLEL_TO`
7. **Quality** - `EFFECTIVE_FOR`, `INEFFECTIVE_FOR`, `PREFERRED_OVER`, `DEPRECATED_BY`, `VALIDATED_BY`

## Installation

### Prerequisites
- Python 3.10 or higher
- Neo4j database (local or cloud)
- Claude Code with MCP support

### Setup

1. Clone the repository:
```bash
git clone https://github.com/viralvoodoo/claude-code-memory.git
cd claude-code-memory
```

2. Install dependencies:
```bash
pip install -e .
```

3. Set up Neo4j connection:
```bash
cp .env.example .env
# Edit .env with your Neo4j credentials
```

4. Initialize the database schema:
```bash
python -m claude_memory.setup
```

## Configuration

### Environment Variables
- `NEO4J_URI` - Neo4j database URI (default: bolt://localhost:7687)
- `NEO4J_USER` - Database username (default: neo4j)
- `NEO4J_PASSWORD` - Database password
- `MEMORY_LOG_LEVEL` - Logging level (default: INFO)

### Claude Code Integration
Add to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "claude-memory": {
      "command": "python",
      "args": ["-m", "claude_memory.server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "your-password"
      }
    }
  }
}
```

## Usage

### Available MCP Tools

#### Core Memory Operations
- `store_memory` - Store new development memories with context
- `get_memory` - Retrieve specific memory by ID with relationships
- `search_memories` - Find memories by content, context, or relationships
- `update_memory` - Modify existing memory content
- `delete_memory` - Remove memory and cleanup relationships

#### Relationship Management
- `create_relationship` - Link memories with specific relationship types
- `get_related_memories` - Find memories connected to a specific memory
- `analyze_relationships` - Discover relationship patterns in memory graph

#### Development Intelligence
- `analyze_codebase` - Scan project and create contextual memory graph
- `track_task_execution` - Record development workflow and patterns
- `suggest_similar_solutions` - Find analogous past solutions
- `predict_solution_effectiveness` - Estimate success probability of approaches

#### Advanced Analytics
- `get_memory_graph` - Visualize knowledge network and relationships
- `find_memory_paths` - Discover connection chains between concepts
- `memory_effectiveness` - Track and analyze solution success rates

## Development

### Project Structure
```
claude-code-memory/
├── src/claude_memory/          # Main source code
│   ├── __init__.py
│   ├── server.py              # MCP server implementation
│   ├── models.py              # Data models and schemas
│   ├── database.py            # Neo4j database operations
│   ├── memory_store.py        # Core memory logic
│   ├── relationships.py       # Relationship management
│   ├── search.py              # Search and retrieval
│   └── intelligence.py        # Pattern recognition and analytics
├── tests/                     # Test suite
├── docs/                      # Documentation
├── scripts/                   # Utility scripts
└── pyproject.toml            # Project configuration
```

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src/ tests/
ruff --fix src/ tests/

# Type checking
mypy src/
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Check existing [GitHub Issues](https://github.com/viralvoodoo/claude-code-memory/issues)
2. Fork the repository and create a feature branch
3. Make changes following our coding standards
4. Add tests for new functionality
5. Submit a pull request with a clear description

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Roadmap

### Phase 1: Foundation (Current)
- ✅ Project setup and basic MCP server
- 🔄 Core memory operations (CRUD)
- ⏳ Basic relationship management

### Phase 2: Intelligence
- ⏳ Advanced relationship system
- ⏳ Pattern recognition
- ⏳ Context awareness

### Phase 3: Integration
- ⏳ Claude Code workflow integration
- ⏳ Automatic memory capture
- ⏳ Proactive suggestions

### Phase 4: Analytics
- ⏳ Memory effectiveness tracking
- ⏳ Knowledge graph visualization
- ⏳ Performance optimization

## Support

- [GitHub Issues](https://github.com/viralvoodoo/claude-code-memory/issues) - Bug reports and feature requests
- [Discussions](https://github.com/viralvoodoo/claude-code-memory/discussions) - Questions and community support
- [Documentation](docs/) - Detailed guides and API reference

## Acknowledgments

- [Model Context Protocol](https://github.com/modelcontextprotocol) - Protocol specification and examples
- [Neo4j](https://neo4j.com/) - Graph database platform
- [Claude Code](https://claude.ai/code) - AI-powered development environment