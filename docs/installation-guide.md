# Claude Code CLI Installation Guide

This guide provides step-by-step instructions for installing and configuring the Claude Code CLI on your development machine.

## Prerequisites

- An Anthropic account with access to Claude Code
- Node.js (version 16 or later)
- npm (version 7 or later)
- Git (version 2.25 or later)

## Installation Steps

### 1. Install Claude Code CLI

Execute the following command in your terminal:

```bash
npm install -g @anthropic/claude-code
```

Alternative installation using curl (if offered by Anthropic):

```bash
curl -fsSL https://get.anthropic.com/claude-code | sh
```

### 2. Verify Installation

Verify the installation by checking the version:

```bash
claude --version
```

You should see the current version of Claude Code displayed.

### 3. Configure Authentication

Run the following command to configure authentication:

```bash
claude auth login
```

Follow the prompts to authenticate with your Anthropic account.

### 4. Test Basic Installation

Test your installation with a simple query:

```bash
claude "What is Claude Code?"
```

You should receive a response from Claude explaining Claude Code.

### 5. Configure Default Settings (Optional)

Create a configuration file to set default options:

```bash
claude config init
```

This will create a configuration file that you can edit to set your preferred defaults.

## Troubleshooting

### Common Issues and Solutions

1. **Authentication Issues**:
   - Ensure you have a valid Anthropic account with Claude Code access
   - Try logging out and logging back in: `claude auth logout` followed by `claude auth login`

2. **Command Not Found**:
   - Ensure npm global bin directory is in your PATH
   - Try installing with sudo/administrator privileges if needed

3. **Version Conflicts**:
   - Check if you have multiple installations: `which -a claude`
   - Remove old versions and reinstall

## Additional Resources

- [Official Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [API Reference](https://docs.anthropic.com/claude-code/api)
- [Community Forums](https://community.anthropic.com)

## Support

For additional help or support:
- Contact Anthropic support: support@anthropic.com
- Visit the help center: https://help.anthropic.com

---

Document version: 1.0
Last updated: May 17, 2025