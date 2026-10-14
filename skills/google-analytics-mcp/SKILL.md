---
name: google-analytics-mcp
description: "Connect Hermes to Google Analytics via MCP."
version: "1.0.0"
author: "Hermes Agent"
license: "MIT"
metadata:
  hermes:
    tags: ["google-analytics","mcp","analytics"]
    related_skills: []
---

Use when you need to connect Hermes to Google Analytics via the Model Context Protocol (MCP) to run reports, manage properties, or execute admin tasks.

## When to Use
You need to pull data from Google Analytics (e.g., sessions, users, events) or administer properties (create, update, list) from within Hermes without leaving the chat. This skill provides the MCP server that enables those operations.

## Procedure
1. **Prepare Google Cloud project**
   - Enable Google Analytics Admin API and Google Analytics Data API.
   - Create OAuth 2.0 Desktop app credentials.
   - Download the JSON key file and note its path.

2. **Set environment variable for Hermes**
   ```bash
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\ga-oauth.json"
   ```
   (Run in Hermes terminal before proceeding.)

3. **Install the Google Analytics MCP skill from the Hermes catalog**
   ```bash
   hermes skill install google-analytics-mcp
   ```
   - A consent card appears; click **Install** and wait for completion.

4. **Activate the MCP server provided by the skill**
   ```bash
   hermes mcp install google-analytics-mcp
   ```
   - A Google OAuth consent screen appears; sign in with the account that has access to the desired Analytics property and grant the requested scopes.

5. **Verify the connection**
   ```bash
   hermes mcp status google-analytics-mcp
   ```
   - Ensure the output shows `"connected": true`. If not, repeat step 4 and confirm the environment variable is set.

6. **Use MCP tools**
   - List available tools:
     ```bash
     hermes tool describe mcp__google_analytics__*
     ```
   - Example: run a basic report
     ```bash
     hermes tool call mcp__google_analytics__run_report '{ "property": "properties/123456789", "dateRanges": [{ "startDate": "7daysAgo", "endDate": "today" }], "metrics": [{ "name": "sessions" }], "dimensions": [{ "name": "date" }] }'
     ```
   - Replace `properties/123456789` with your GA4 property ID (found in GA → Admin → Property Settings).

## Pitfalls
- **Missing OAuth credentials** – If the `GOOGLE_APPLICATION_CREDENTIALS` variable is not set, the MCP server will fail to authenticate; always set it in the same terminal session before installing/activating the MCP.
- **Wrong property ID format** – Use the full resource name `properties/GA4_PROPERTY_ID`; using only the numeric ID will cause “not found” errors.
- **Scope consent** – The OAuth screen requests access to Analytics Admin and Data API; denying any scope will result in connection failure; grant all requested scopes.
- **Skill not found in catalog** – Ensure the Hermes catalog plugin is enabled; if `hermes skill install` returns “skill not found”, run `hermes catalog refresh` or restart Hermes to sync the catalog.

## References
- `references/property-id-lookup.md` – How to find the GA4 property ID.
- `references/oauth-errors.md` – Common OAuth consent errors and fixes.
