# MCP Server Configuration Guide

This guide explains how to configure and use Model Context Protocol (MCP) servers with Claude Code in our project.

## What is MCP?

Model Context Protocol (MCP) is an open protocol that enables language models like Claude to access external tools and data sources. This allows Claude to perform specialized tasks such as querying databases, analyzing code, generating documentation, and more.

## Server Scopes

MCP servers can be configured at three different scopes:

1. **Local** (default): Available only to you in the current project
2. **Project**: Shared with everyone in the project via `.mcp.json` file
3. **User**: Available to you across all projects

## Configuring MCP Servers

### Basic MCP Server Configuration

To add a new MCP server:

```bash
claude mcp add <server-name> --command <command-to-start-server> [options]
```

Example:

```bash
claude mcp add postgres-mcp --command "node mcp-config/postgres-mcp-server.js" --env DB_USER=user --env DB_PASS=pass
```

### Scope Options

Use the `-s` or `--scope` flag to specify where the configuration is stored:

```bash
# Local scope (default)
claude mcp add postgres-mcp --command "node mcp-config/postgres-mcp-server.js" -s local

# Project scope (shared via .mcp.json)
claude mcp add postgres-mcp --command "node mcp-config/postgres-mcp-server.js" -s project

# User scope (available across all projects)
claude mcp add postgres-mcp --command "node mcp-config/postgres-mcp-server.js" -s user
```

### Environment Variables

Set environment variables with the `-e` or `--env` flags:

```bash
claude mcp add postgres-mcp --command "node mcp-config/postgres-mcp-server.js" -e DB_HOST=localhost -e DB_PORT=5432
```

### Managing MCP Servers

List all configured servers:

```bash
claude mcp list
```

Remove a server:

```bash
claude mcp remove <server-name>
```

Check MCP server status during a Claude Code session:

```
/mcp
```

## Project MCP Servers

Our project uses the following MCP servers:

### 1. PostgreSQL MCP Server

Provides read-only access to PostgreSQL databases for querying and schema inspection.

**Capabilities**:
- Execute read-only SQL queries
- List tables in the database
- Describe table structure

**Configuration**:
```json
{
  "name": "postgres-mcp",
  "type": "stdio",
  "command": "node mcp-config/postgres-mcp-server.js",
  "environment": {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_USER": "claude_user",
    "DB_PASSWORD": "secure_password_here",
    "DB_NAME": "claude_project"
  }
}
```

### 2. Code Review Server

Analyzes code quality and provides suggestions for improvement.

**Capabilities**:
- Static code analysis
- Style checking
- Security vulnerability scanning
- Performance issue detection

**Configuration**:
```json
{
  "name": "code-review",
  "type": "stdio",
  "command": "node mcp-config/code-review-server.js",
  "environment": {}
}
```

### 3. Documentation Generator

Automatically generates documentation from code.

**Capabilities**:
- Generate code documentation
- Create README files
- Build API references
- Produce user guides

**Configuration**:
```json
{
  "name": "doc-generator",
  "type": "stdio",
  "command": "node mcp-config/doc-generator-server.js",
  "environment": {
    "TEMPLATE_DIR": "./templates/documentation"
  }
}
```

### 4. Test Generator

Creates test cases for code.

**Capabilities**:
- Generate unit tests
- Create integration tests
- Build test fixtures
- Suggest test coverage improvements

**Configuration**:
```json
{
  "name": "test-generator",
  "type": "stdio",
  "command": "node mcp-config/test-generator-server.js",
  "environment": {
    "TEST_FRAMEWORK": "jest"
  }
}
```

## Security Considerations

- MCP servers run with the same permissions as the Claude Code process
- Only use MCP servers from trusted sources
- Be especially careful with MCP servers that connect to the internet
- Review MCP server code before using it
- Use read-only access where possible (e.g., database queries)

## Troubleshooting

### Server Not Starting

1. Check if the command is correct
2. Verify all required environment variables are set
3. Look for error messages in the Claude Code output

### Connection Issues

1. Ensure the server is running
2. Check if the server is listening on the expected port
3. Verify network configuration if connecting to remote services

### Configuration Problems

1. Use `claude mcp list` to check current configuration
2. Reset choices with `claude mcp reset-project-choices`
3. Check the `.mcp.json` file for syntax errors

## References

- [Model Context Protocol Documentation](https://modelcontextprotocol.io/introduction)
- [Claude Code MCP Documentation](https://docs.anthropic.com/claude-code/mcp)
