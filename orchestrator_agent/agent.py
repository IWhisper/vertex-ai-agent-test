from google.adk.agents import Agent
from vertexai.agent_engines import AdkApp

from .instructions import ORCHESTRATOR_INSTRUCTIONS
from sub_agents.rss_agent.agent import rss_agent
from sub_agents.market_agent.agent import market_agent

# The Boss Agent
orchestrator_agent = Agent(
    name="orchestrator_agent",
    description="The main orchestrator gateway. Routes user tracking and summary requests to the appropriate financial or news sub-agents.",
    model="gemini-2.5-flash-lite", # Use a slightly smarter model for reasoning and routing
    instruction=ORCHESTRATOR_INSTRUCTIONS,
    # Here is where the magic happens: by explicit pass, the orchestrator knows these are its transferrable sub-agents!
    sub_agents=[rss_agent, market_agent]
)


# ─────────────────────────────────────────────────────────────────────────────
# ABOUT AdkApp AND ITS DEFAULT INTERFACE
# ─────────────────────────────────────────────────────────────────────────────
#
# AdkApp is designed around *streaming* because LLM agent responses are
# inherently async: tools get called, sub-agents are invoked, each step
# produces partial results. Therefore AdkApp only exposes streaming out of
# the box:
#
#   stream_query(user_id, message)        — sync  stream (yields dicts)
#   async_stream_query(user_id, message)  — async stream (yields dicts)
#
# There is deliberately NO blocking `query()` method built into AdkApp.
#
# If you only need this default streaming interface, you can keep it simple:
#
#   app = AdkApp(agent=orchestrator_agent)
#
# ...and in deploy_from_source.py, only register stream_query:
#
#   "class_methods": [
#       {
#           "name": "stream_query",
#           "api_mode": "stream",
#           "parameters": { ... }
#       }
#   ]
#
# ABOUT OrchestratorApp (this file)
# ─────────────────────────────────────────────────────────────────────────────
# We subclass AdkApp to add a server-side `query()` method that collects
# the stream internally and returns only the final text. This lets callers
# choose between:
#   • stream_query → real-time chunks (useful for UIs / progress display)
#   • query        → single blocking response (useful for simple scripts /
#                    pipelines that just want the final answer)
#
# NOTE: In test_deployed.py, our --mode sync also achieves "blocking" by
# consuming stream_query on the *client* side. The server-side query() method
# is an alternative approach that offloads the collection to the server.
# ─────────────────────────────────────────────────────────────────────────────


class OrchestratorApp(AdkApp):
    """
    Extended AdkApp with an additional blocking `query()` endpoint. (for demo)

    - `stream_query(user_id, message)` → yields chunks in real-time (streaming)
    - `query(user_id, message)`        → waits for completion, returns final text
    """

    def query(self, *, user_id: str, message: str, session_id: str = None) -> str:
        """
        Non-streaming, blocking query. Internally drives stream_query and
        returns only the last text chunk (the agent's final response).
        """
        final_text = ""
        for chunk in self.stream_query(
            user_id=user_id,
            message=message,
            session_id=session_id,
        ):
            # Each chunk from stream_query is a dict with content parts
            if isinstance(chunk, dict):
                for part in chunk.get("content", {}).get("parts", []):
                    if "text" in part and part["text"]:
                        final_text = part["text"]  # keep the latest text chunk
        return final_text


# Wrap the orchestrator in our extended AdkApp.
# Use `app = AdkApp(agent=orchestrator_agent)` instead if you only
# want the default stream_query interface and don't need blocking query().
app = OrchestratorApp(agent=orchestrator_agent)
