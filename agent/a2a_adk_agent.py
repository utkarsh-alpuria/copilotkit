from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.genai import types
from google.adk.tools import agent_tool
import os
from dotenv import load_dotenv
from google.adk.planners import PlanReActPlanner, BuiltInPlanner
import json
from typing import Dict, Any, List, Optional
from google.adk.models.lite_llm import LiteLlm
import litellm
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
from fastapi import FastAPI

load_dotenv()
litellm.ssl_verify = False

lite_llm_model = LiteLlm(
        model=f"azure/{os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")}",
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )
# lite_llm_model = LiteLlm(
#         model=f"openai/{os.getenv("OPENAI_MODEL_NAME")}",
#         api_key=os.getenv("OPENAI_API_KEY"),
#     )
# lite_llm_model = LiteLlm(
#         model=f"gemini/{os.getenv("GEMINI_MODEL_NAME")}",
#         api_key=os.getenv("GEMINI_API_KEY"),
#     )

agent_name = "github_agent"
agent_description="An agent for git/github related tasks"

agent_card_url = f"{'http://localhost:10000'}{AGENT_CARD_WELL_KNOWN_PATH}"
print("CARD URL - ", agent_card_url)
remote_a2a_agent = RemoteA2aAgent(
            name=agent_name,
            description=agent_description,
            agent_card=agent_card_url,
        )
tool_agent = agent_tool.AgentTool(remote_a2a_agent)

agent = LlmAgent(
        name="github_local_agent",
        model=lite_llm_model,
        instruction = "You are a specialized agent which has access to a tool agent for specific tasks. Your task is to pass user queries to tool agent get the result from it and provide it to user",
        tools=[tool_agent]
    )

# Create ADK middleware agent instance
adk_agent = ADKAgent(
    adk_agent=agent,
    # app_name="orchestrator_app",
    app_name="agents",
    user_id="demo_user",
)

app = FastAPI(title="ADK Middleware Proverbs Agent")

# Add the ADK endpoint
# add_adk_fastapi_endpoint(app, adk_agent, path="/orchestrator")
add_adk_fastapi_endpoint(app, adk_agent, path="/agent")

if __name__ == "__main__":
    import os
    import uvicorn


    port = int(os.getenv("PORT", 9000))
    uvicorn.run(app, host="0.0.0.0", port=port)