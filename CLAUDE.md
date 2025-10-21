# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a minimal repository currently containing only configuration files. The repository is located at `C:\Code\script\information` and is **not** a git repository.

## MCP Server Configuration

The repository has the Context7 MCP server configured in `.mcp.json`, which provides access to up-to-date documentation and code examples for various libraries.

**MCP Server Details:**
- **Server Name:** context7-mcp
- **Purpose:** Retrieve library documentation and code examples
- **API Key:** Configured (9394d24c-5f1f-4e11-871d-7959f9920789)

To use the Context7 MCP server:
1. First resolve the library ID: `resolve-library-id` with the library name
2. Then fetch documentation: `get-library-docs` with the Context7-compatible library ID

## Claude Code Settings

Local settings are configured in `.claude/settings.local.json`:
- All project MCP servers are enabled
- Bash commands with `dir:*` pattern are permitted
- The context7-mcp server is explicitly enabled

## Development Notes

This appears to be a workspace for script development or information gathering. There are currently no source code files, build configurations, or package managers configured.

When adding code to this repository, consider:
- Initializing as a git repository if version control is needed
- Adding a README.md to document the purpose and usage
- Setting up appropriate build/test tooling based on the chosen language
