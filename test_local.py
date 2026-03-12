import os
import asyncio
import time
from dotenv import dotenv_values

# CRITICAL: Set these BEFORE importing anything from google.adk or google.genai
# ADK reads these at module load time to decide which LLM backend to use.
# We use dotenv_values (not load_dotenv) to explicitly set each var before any imports.
_env = dotenv_values(".env")
os.environ["GOOGLE_CLOUD_PROJECT"] = _env["GOOGLE_CLOUD_PROJECT"]
os.environ["GOOGLE_CLOUD_LOCATION"] = _env["GOOGLE_CLOUD_LOCATION"]
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"

from google.adk.runners import InMemoryRunner
from google.genai import types as genai_types
from orchestrator_agent.agent import orchestrator_agent


async def run_query(runner: InMemoryRunner, session, query: str) -> str:
    """Sends a query and collects the final text response from the agent."""
    content = genai_types.Content(
        role="user",
        parts=[genai_types.Part(text=query)]
    )
    
    final_text = ""
    print("  [Debug Events]:")
    async for event in runner.run_async(
        user_id=session.user_id,
        session_id=session.id,
        new_message=content
    ):
        author = getattr(event, "author", "?")
        actions = getattr(event, "actions", None)
        
        # Show routing handoff
        if actions and getattr(actions, "transfer_to_agent", None):
            print(f"    🔄 [{author}] → [{actions.transfer_to_agent}]")
        
        # Show tool calls and responses + accumulate final text
        if event.content and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "function_call") and part.function_call:
                    print(f"    🛠️  [{author}] calling → {part.function_call.name}({dict(part.function_call.args)})")
                elif hasattr(part, "function_response") and part.function_response:
                    result = str(part.function_response.response.get("result", ""))
                    snippet = result[:150].replace("\n", " ") + ("..." if len(result) > 150 else "")
                    print(f"    📦 [{author}] result → {snippet}")
                elif hasattr(part, "text") and part.text:
                    # Capture text from any agent; the last text will be the final reply
                    final_text = part.text  # Replace (not append) so we get the latest response
    
    return final_text


async def main():
    print("=== Testing Local Orchestrator Agent (via InMemoryRunner) ===\n")
    
    runner = InMemoryRunner(agent=orchestrator_agent, app_name="orchestrator")
    session = await runner.session_service.create_session(
        app_name="orchestrator",
        user_id="test-user",
    )
    
    test_queries = [
        "Can you do both? Give me a brief market summary and then summarize the news.",
        # "What are the major news from this RSS feed: https://www.gelonghui.com/api/live-channels/all/lives/v4?category=important&limit=15",
        # "How is the US stock market doing today? Tell me about the top tech stocks.",
    ]

    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"User Query:\n  {query}")
        print(f"{'='*60}")
        try:
            response = await run_query(runner, session, query)
            print(f"\n  --- [Agent Final Output] ---")
            print(response)
        except Exception as e:
            print(f"\n  Error: {e}")
        
        time.sleep(5)  # Brief pause to avoid 429 Quota limits


if __name__ == "__main__":
    asyncio.run(main())
