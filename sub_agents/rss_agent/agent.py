from google.adk.agents import Agent

from .instructions import RSS_AGENT_INSTRUCTIONS
from .tools import fetch_rss_feed

rss_agent = Agent(
    name="rss_summarizer_agent",
    description="A specialized agent that fetches content from an RSS feed or JSON URL and summarizes the major news and trends. Useful for requests involving news topics or summaries of links.",
    model="gemini-2.5-flash-lite",
    instruction=RSS_AGENT_INSTRUCTIONS,
    tools=[fetch_rss_feed],
)
