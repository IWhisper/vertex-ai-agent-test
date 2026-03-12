from google.adk.agents import Agent
from datetime import date

from .instructions import get_market_agent_instructions
from .tools import fetch_major_indices, fetch_top_tech_stocks

market_agent = Agent(
    name="market_analyst_agent",
    description="A specialized financial analyst agent. Useful for checking the current performance of the US stock market, major indices, and top technology stocks.",
    model="gemini-2.5-flash-lite",
    instruction=get_market_agent_instructions(date.today().strftime("%Y-%m-%d")),
    tools=[fetch_major_indices, fetch_top_tech_stocks],
)
