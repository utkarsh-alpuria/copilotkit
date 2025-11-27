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
 
export async function POST(request: NextRequest) {
  const inventoryAgentUrl = "http://localhost:8001";
 
  const orchestratorUrl = process.env.ORCHESTRATOR_URL || "http://localhost:9000/orchestrator";
 
  // Connect to orchestrator via AG-UI Protocol
  const orchestrationAgent = new HttpAgent({
    url: orchestratorUrl,
  });
  // const inventoryAgent = new HttpAgent({
  //   url: inventoryAgentUrl,
  // });
 
  // A2A Middleware: Wraps orchestrator and injects send_message_to_a2a_agent tool
  // This allows orchestrator to communicate with A2A agents transparently
  const a2aMiddlewareAgent = new A2AMiddlewareAgent({
    description:
      "Orchestrator with Git Local MCP agent and Inventory A2A agent",
    agentUrls: [
      inventoryAgentUrl
    ],
    orchestrationAgent,
    instructions: `
     You are an orchestrator agent with access to multiple agents and tools, call appropriate agent and tools according to user queries to complete the task.
    `,
  });
 
 
  // const a2aMiddlewareAgent = new A2AMiddlewareAgent({
  //   description:"An Inventory agent",
  //   inventoryAgent,
  //   instructions: "You are a inventory management assistant with access to inventory products.",
  // });
 
  // CopilotKit runtime connects frontend to agent system
  const runtime = new CopilotRuntime({
    agents: {
      "my_agent" : new HttpAgent({
    url: orchestratorUrl,
  }),
      a2a_chat: a2aMiddlewareAgent, // Must match agent prop in <CopilotKit agent="a2a_chat">
    },
  });
 
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });
 
  return handleRequest(request);
}
 
 