# 

"""Shared State feature."""

# from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()
import json
from fastapi import FastAPI
from ag_ui_adk import ADKAgent, add_adk_fastapi_endpoint
# ADK imports
from google.adk.agents import LlmAgent
from google.genai import types

from typing import List, Optional

import litellm
from google.adk.models.lite_llm import LiteLlm
import asyncio
import os
import logging

litellm.ssl_verify = False

import logging
import sys

# Create handlers
console_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler("app.log", mode="a")  # saves logs to app.log

# Common log format
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

console_handler.setFormatter(log_format)
file_handler.setFormatter(log_format)

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    handlers=[console_handler, file_handler]  # send logs to both console and file
)

# Example log
logging.debug("Logging initialized with file logging enabled.")


# lite_llm_model = LiteLlm(
#         model=f"azure/{os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")}",
#         api_key=os.getenv("AZURE_OPENAI_API_KEY"),
#         api_base=os.getenv("AZURE_OPENAI_ENDPOINT"),
#         api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
#     )
lite_llm_model = LiteLlm(
        model=f"gemini/{os.getenv("GEMINI_MODEL_NAME")}",
        api_key=os.getenv("GEMINI_API_KEY"),
    )

agent = LlmAgent(
        name="OrchesratorAgent",
        model=lite_llm_model,
        instruction=f"""
           You are an orchestrator agent with access to multiple agents and tools, call appropriate agent and tools according to user queries to complete the task.
        """,
    )

# Create ADK middleware agent instance
adk_agent = ADKAgent(
    adk_agent=agent,
    # app_name="orchestrator_app",
    app_name="agents",
    user_id="demo_user",

)

# Create FastAPI app
app = FastAPI(title="ADK Middleware Proverbs Agent")

# Add the ADK endpoint
# add_adk_fastapi_endpoint(app, adk_agent, path="/orchestrator")
add_adk_fastapi_endpoint(app, adk_agent, path="/agent")

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
