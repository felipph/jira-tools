# AI Coding Instructions for jira-tools

This document provides essential guidance for AI agents working with the jira-tools codebase.

## Project Overview

jira-tools is a Python-based integration library that provides LangChain tools for interacting with Jira. It enables AI agents to perform Jira operations through a clean API layer.

### Core Components

- **Core Integration** (`src/core/jira/jira_integration.py`): Contains the base Jira integration logic and implementation functions
- **LangChain Tools** (`src/tools/langchain/jira_tools.py`): Exposes Jira operations as LangChain tools
- **Configuration** (`config.py`): Manages field blacklists and configuration settings

## Key Architecture Patterns

1. **Decorator Pattern**: Uses `@with_jira_client` decorator to ensure Jira client initialization before operations
   ```python
   @with_jira_client
   def get_issue_details(issue_key: str) -> Dict[str, str]:
   ```

2. **Environment Configuration**: Uses `.env` file for Jira credentials:
   - `JIRA_URL`: Jira server URL
   - `JIRA_ACCOUNT_EMAIL`: Account email
   - `JIRA_API_TOKEN`: API token for authentication

3. **Field Blacklisting**: Implements type-specific and global field blacklists in `config.py`

## Common Operations

### Creating Issues
```python
create_jira_issue(
    project="PROJ",
    parent="PROJ-123",
    assignee_email="user@example.com",
    title="Issue Title",
    issue_type="Tarefa",
    description="Description",
    custom_fields={}
)
```

### Managing Issue Transitions
```python
transitions = get_jira_transitions("PROJ-123")
transition_jira_issue("PROJ-123", "In Progress")
```

## Development Setup

1. Python 3.12+ required
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create `.env` file with Jira credentials

## Best Practices

1. Always use the `@with_jira_client` decorator for functions that need Jira access
2. Handle custom fields according to the blacklist configuration
3. Use rich text (wiki markup) for issue descriptions
4. Validate user existence before assigning issues
5. Handle transitions by name rather than ID for better readability

## Error Handling

- Check for user existence before assigning issues
- Validate transition names against available transitions
- Handle parent issue relationships appropriately

## Testing

Always test Jira operations with:
1. Valid and invalid credentials
2. Various issue types
3. Different transition states
4. Custom field combinations
