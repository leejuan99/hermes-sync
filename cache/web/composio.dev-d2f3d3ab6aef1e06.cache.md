# Metaads MCP for AI Agents

Securely connect your AI agents and chatbots (Claude, ChatGPT, Cursor, etc) with Metaads MCP or direct API to create campaigns, pull ad performance data, update budgets, and generate custom reports through natural language.

![Metaads logo](https://logos.composio.dev/api/metaads)Metaads

Oauth2Api Key

Metaads is Meta's official Ads API that lets you manage, analyze, and optimize your Facebook and Instagram ad campaigns. Streamline ad operations and gain deeper insights with robust automation.

50 Tools

## Try Metaads now

Type what you want done — sign in and watch it run live in the Tool Router playground.

TOOL ROUTER PLAYGROUND

Metaads

Try asking

TOOLS

## Supported Tools

Every Metaads action and event your agent gets out of the box.

SETUP GUIDE

## Connect Metaads MCP Tool with your Agent

1

#### Install Composio

typescript

```
npm install @composio/core ai @ai-sdk/openai @ai-sdk/mcp
```

Install the Composio SDK and Claude Agent SDK

2

#### Create Tool Router Session

typescript

```
import { Composio } from '@composio/core';

const composio = new Composio({ apiKey: 'your-api-key' });

console.log("Creating Tool Router session...");
const { mcp } = await composio.create('your-user-id');
console.log(`Tool Router session created: ${mcp.url}`);
```

Initialize the Composio client and create a Tool Router session

3

#### Connect to AI Agent

typescript

```
import { openai } from '@ai-sdk/openai';
import { experimental_createMCPClient as createMCPClient } from '@ai-sdk/mcp';
import { generateText, stepCountIs } from 'ai';

const client = await createMCPClient({
  transport: {
    type: 'http',
    url: mcp.url,
    headers: { 'x-api-key': 'your-composio-api-key' }
  }
});

const tools = await client.tools();

const { text } = await generateText({
  model: openai('gpt-4o'),
  tools,
  messages: [{ role: 'user', content: 'Get insights for campaign 12345 from last week' }],
  stopWhen: stepCountIs( 5 )
});

console.log(`Agent: ${text}`);
```

Use the MCP server with your AI agent

SETUP GUIDE

## Connect Metaads API Tool with your Agent

1

#### Install Composio

typescript

```
npm install @composio/openai
```

Install the Composio SDK

2

#### Initialize Composio and Create Tool Router Session

typescript

```
import OpenAI from 'openai';
import { Composio } from '@composio/core';
import { OpenAIResponsesProvider } from '@composio/openai';

const composio = new Composio({
  provider: new OpenAIResponsesProvider(),
});
const openai = new OpenAI({});
const session = await composio.create('your-user-id');
```

Import and initialize Composio client, then create a Tool Router session

3

#### Execute Metaads Tools via Tool Router with Your Agent

typescript

```
const tools = session.tools;
const response = await openai.responses.create({
  model: 'gpt-4.1',
  tools: tools,
  input: [{
    role: 'user',
    content: 'Get insights for my latest ad campaign this week'
  }],
});
const result = await composio.provider.handleToolCalls(
  'your-user-id',
  response.output
);
console.log(result);
```

Get tools from Tool Router session and execute Metaads actions with your Agent

## Why Use Composio?

### AI Native Metaads Integration

- Supports both Metaads MCP and direct API based integrations
- Structured, LLM-friendly schemas for reliable tool execution
- Rich coverage for reading, writing, and querying your Metaads data

### Managed Auth

- Built-in OAuth handling with automatic token refresh and rotation
- Central place to manage, scope, and revoke Metaads access
- Per user and per environment credentials instead of hard-coded keys

### Agent Optimized Design

- Tools are tuned using real error and success rates to improve reliability over time
- Comprehensive execution logs so you always know what ran, when, and on whose behalf

### Enterprise Grade Security

- Fine-grained RBAC so you control which agents and users can access Metaads
- Scoped, least privilege access to Metaads resources
- Full audit trail of agent actions to support review and compliance

FAQ

## Frequently asked questions

###

Yes, Metaads requires you to configure your own OAuth credentials. Once set up, Composio handles token storage, refresh, and lifecycle management for you.

###

Yes! Composio's Tool Router enables agents to use multiple toolkits. [Learn more](https://docs.composio.dev/tool-router/overview).

###

Composio is SOC 2 and ISO 27001 compliant with all data encrypted in transit and at rest. [Learn more](https://trust.composio.dev).

###

Composio maintains and updates all toolkit integrations automatically, so your agents always work with the latest API versions.

## Start with Metaads.It takes 30 seconds.

Managed auth, hosted MCP servers, and every Metaads tool your agent needs.Free to start.

[Start building](https://dashboard.composio.dev/login?cta_placement=toolkit-metaads-final-cta)