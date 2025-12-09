# 

"""Shared State feature."""

from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()
import json
from enum import Enum
from typing import Dict, List, Any, Optional
from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint

# ADK imports
from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner
from google.adk.events import Event, EventActions
from google.adk.tools import FunctionTool, ToolContext
from google.genai.types import Content, Part , FunctionDeclaration
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams,StreamableHTTPConnectionParams
import litellm
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset
from google.adk.models.lite_llm import LiteLlm
import asyncio
import os

litellm.ssl_verify = False

class ProverbsState(BaseModel):
    """List of the proverbs being written."""
    proverbs: list[str] = Field(
        default_factory=list,
        description='The list of already written proverbs',
    )


def set_proverbs(
  tool_context: ToolContext,
  new_proverbs: list[str]
) -> Dict[str, str]:
    """
    Set the list of provers using the provided new list.

    Args:
        "new_proverbs": {
            "type": "array",
            "items": {"type": "string"},
            "description": "The new list of proverbs to maintain",
        }

    Returns:
        Dict indicating success status and message
    """
    try:
        # Put this into a state object just to confirm the shape
        new_state = { "proverbs": new_proverbs}
        tool_context.state["proverbs"] = new_state["proverbs"]
        return {"status": "success", "message": "Proverbs updated successfully"}

    except Exception as e:
        return {"status": "error", "message": f"Error updating proverbs: {str(e)}"}



def get_weather(tool_context: ToolContext, location: str) -> Dict[str, str]:
    """Get the weather for a given location. Ensure location is fully spelled out."""
    return {"status": "success", "message": f"The weather in {location} is sunny."}



def on_before_agent(callback_context: CallbackContext):
    """
    Initialize proverbs state if it doesn't exist.
    """

    if "proverbs" not in callback_context.state:
        # Initialize with default recipe
        default_proverbs =     []
        callback_context.state["proverbs"] = default_proverbs


    return None




# --- Define the Callback Function ---
#  modifying the agent's system prompt to incude the current state of the proverbs list
def before_model_modifier(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Inspects/modifies the LLM request or skips the call."""
    agent_name = callback_context.agent_name
    if agent_name == "ProverbsAgent":
        proverbs_json = "No proverbs yet"
        if "proverbs" in callback_context.state and callback_context.state["proverbs"] is not None:
            try:
                proverbs_json = json.dumps(callback_context.state["proverbs"], indent=2)
            except Exception as e:
                proverbs_json = f"Error serializing proverbs: {str(e)}"
        # --- Modification Example ---
        # Add a prefix to the system instruction
        original_instruction = llm_request.config.system_instruction or types.Content(role="system", parts=[])
        prefix = f"""You are a helpful assistant for maintaining a list of proverbs.
        This is the current state of the list of proverbs: {proverbs_json}
        When you modify the list of proverbs (wether to add, remove, or modify one or more proverbs), use the set_proverbs tool to update the list."""
        # Ensure system_instruction is Content and parts list exists
        if not isinstance(original_instruction, types.Content):
            # Handle case where it might be a string (though config expects Content)
            original_instruction = types.Content(role="system", parts=[types.Part(text=str(original_instruction))])
        if not original_instruction.parts:
            original_instruction.parts.append(types.Part(text="")) # Add an empty part if none exist

        # Modify the text of the first part
        modified_text = prefix + (original_instruction.parts[0].text or "")
        original_instruction.parts[0].text = modified_text
        llm_request.config.system_instruction = original_instruction



    return None






# --- Define the Callback Function ---
def simple_after_model_modifier(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Stop the consecutive tool calling of the agent"""
    agent_name = callback_context.agent_name
    # --- Inspection ---
    if agent_name == "ProverbsAgent":
        original_text = ""
        if llm_response.content and llm_response.content.parts:
            # Assuming simple text response for this example
            if  llm_response.content.role=='model' and llm_response.content.parts[0].text:
                original_text = llm_response.content.parts[0].text
                callback_context._invocation_context.end_invocation = True

        elif llm_response.error_message:
            return None
        else:
            return None # Nothing to modify
    return None



async def connect_mcp_tool(urls:List, header=None):
        all_tools = []
        for url in urls:
            mcp_conn = StreamableHTTPConnectionParams(
                        url=url,
                    )
            toolset = MCPToolset(connection_params=mcp_conn)
            try:
                tools = await toolset.get_tools()
                for tool in tools:
                    print("---- TOOL ----")
                    print(f"Name: {tool.name}")
                    print(f"Description: {tool.description}")
                all_tools.extend(tools)
            except Exception as e:
                print(f"Error occurred while fetching tools from MCP at {url}: {e}")
            finally:
                if len(all_tools) > 0:
                    await toolset.close()
                print(f"Closed connection to MCP at: {url}")
        return all_tools

# git_mcp_tools = connect_mcp_tool(urls=["http://localhost:3001/mcp"])
loop = asyncio.get_event_loop()
git_mcp_tools = loop.run_until_complete(connect_mcp_tool(urls=["http://localhost:3001/mcp"]))
print(git_mcp_tools)


lite_llm_model = LiteLlm(
        model=f"azure/{os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")}",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
# lite_llm_model = LiteLlm(
#         model=f"gemini/{os.getenv("GEMINI_MODEL_NAME")}",
#         api_key=os.getenv("GEMINI_API_KEY"),
#     )


git_local_agent = LlmAgent(
    name="GitHubAgent",
    model="gemini-2.5-flash",
    tools=git_mcp_tools,
    description="An agent for all git/github related tasks",
    instruction="You are a GitHub operations assistant. Use MCP tools for all git/github related repository-level tasks."
)

orchestrator_agent = LlmAgent(
        name="OrchesratorAgent",
        model=lite_llm_model,
        instruction=f"""
           You are an orchestrator agent with access to multiple agents and tools, call appropriate agent and tools according to user queries to complete the task.
        """,
        # sub_agents = [git_local_agent],
        before_agent_callback=on_before_agent,
        before_model_callback=before_model_modifier,
        after_model_callback = simple_after_model_modifier
    )

# Create ADK middleware agent instance
adk_orchestrator_agent = ADKAgent(
    adk_agent=orchestrator_agent,
    app_name="orchestrator_app",
    user_id="demo_user",
    # session_timeout_seconds=3600,
    # use_in_memory_services=True
)

# Create FastAPI app
app = FastAPI(title="ADK Middleware Proverbs Agent")

# Add the ADK endpoint
add_adk_fastapi_endpoint(app, adk_orchestrator_agent, path="/orchestrator")

if __name__ == "__main__":
    import os
    import uvicorn

    if not os.getenv("GOOGLE_API_KEY"):
        print("⚠️  Warning: GOOGLE_API_KEY environment variable not set!")
        print("   Set it with: export GOOGLE_API_KEY='your-key-here'")
        print("   Get a key from: https://makersuite.google.com/app/apikey")
        print()

    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)
