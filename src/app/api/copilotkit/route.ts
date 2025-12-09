// 

/**
* CopilotKit API Route with A2A Middleware
*
* This connects the frontend to multiple agents using two protocols:
* - AG-UI Protocol: Frontend ↔ Orchestrator (via CopilotKit)
* - A2A Protocol: Orchestrator ↔ Specialized Agents (Research, Analysis)
*
* The A2A middleware injects send_message_to_a2a_agent tool into the orchestrator,
* enabling seamless agent-to-agent communication without the orchestrator needing
* to understand A2A Protocol directly.
*/

import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { A2AMiddlewareAgent } from "@ag-ui/a2a-middleware";
import { NextRequest } from "next/server";
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import type { MCPClient } from "@copilotkit/runtime";

export async function POST(request: NextRequest) {
  // const inventoryAgentUrl = "http://localhost:8001";

  // const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:9000/orchestrator";
  const agentUrl = "http://localhost:9000/agent";

  // Connect to orchestrator via AG-UI Protocol
  const Agent = new HttpAgent({
    url: agentUrl,
  });

  const runtime = new CopilotRuntime({
    agents: {
      "my_agent" : Agent
      // a2a_chat: a2aMiddlewareAgent, // Must match agent prop in <CopilotKit agent="a2a_chat">
    },
  });

  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });

  return handleRequest(request);
}

