---
name: make-mcp-oauth-setup-in-hermes
description: "Set up Make MCP server in Hermes with OAuth."
version: 1.0.0
author: Hermes Agent
license: MIT

---

# Make MCP Setup in Hermes with OAuth

This skill outlines the steps to configure the Make MCP server in Hermes Agent using OAuth authentication.

## When to Use This Skill

Use this skill when you want to connect Hermes to the Make platform via its MCP server to build automation scenarios using Make skills.

## Prerequisites

- A Make account
- Hermes Agent installed and running
- Basic familiarity with Hermes CLI

## Procedure

### 1. Install the Make Skills Repository (Optional but Recommended)

The Make Skills repository contains the MCP configuration for Make. Installing it as a Hermes plugin allows you to reference the configuration, though the plugin itself is designed for Claude Code.

```bash
hermes plugins install https://github.com/integromat/make-skills
```

> **Note**: The plugin may not be recognized as a native Hermes plugin due to missing plugin manifest. This step is optional; you can proceed to manual MCP server configuration.

### 2. Manually Configure the Make MCP Server

Add the Make MCP server to Hermes configuration:

```bash
hermes mcp add make --url https://mcp.make.com
```

### 3. Configure OAuth Authentication

Set the authentication method to OAuth:

```bash
hermes config set mcp_servers.make.auth oauth
```

### 4. Enable the MCP Server

Enable the server so Hermes can connect to it:

```bash
hermes config set mcp_servers.make.enabled true
```

### 5. Test the Connection

Verify that Hermes can reach the MCP server:

```bash
hermes mcp test make
```

If the test fails with an SSL certificate error, proceed to the troubleshooting section.

### 6. Perform OAuth Login

Initiate the OAuth flow to authorize Hermes to access your Make account:

```bash
hermes mcp login make
```

- A URL will be displayed. Open this URL in your web browser.
- Log in to your Make account if prompted.
- Authorize Hermes to access your Make data.
- After authorization, you will be redirected to a local callback URL (e.g., `http://127.0.0.1:<port>/callback`).
- Copy the entire redirect URL from your browser's address bar and paste it back into the Hermes terminal prompt.
- Press Enter to complete the authentication.

### 7. Verify the Setup

Run the test command again to confirm the connection is successful:

```bash
hermes mcp test make
```

You should see a success message.

## Troubleshooting

### SSL Certificate Verification Failed

If you encounter an error like `SSL: CERTIFICATE_VERIFY_FAILED` when testing or logging in, it indicates that Hermes does not trust the server's certificate.

**Resolution Steps**:
1. Ensure your system's certificate store includes the root certificate authority for `mcp.make.com`.
2. If you are in a corporate environment with SSL interception, ensure the interception certificate is trusted by your system.
3. Do not disable certificate verification unless you are in a trusted environment and understand the risks. As a last resort, you can set the environment variable `NODE_TLS_REJECT_UNAUTHORIZED=0` before starting Hermes, but this is insecure and not recommended for production.

### OAuth Flow Issues

If the OAuth flow fails after pasting the redirect URL:
- Ensure you copied the full URL, including the `code` and `state` parameters.
- Check that the Make application OAuth client ID is correct and authorized for MCP access.
- Try the login process again; sometimes transient network issues occur.

## Notes

- The Make MCP server URL is `https://mcp.make.com`.
- The OAuth client ID for the Make MCP server is `b47d961e-3339-430a-a728-938d78d4746c` (as seen in the authorization URL).
- After successful setup, you can use Make MCP tools in Hermes, such as `apps_recommend`, `app_modules_list`, and `scenarios_create`, to build automation scenarios.

## References

- Make MCP Documentation: https://www.make.com/en/mcp
- Hermes MCP Guide: https://hermes-agent.nousresearch.com/docs/user-guide/features/mcp/
