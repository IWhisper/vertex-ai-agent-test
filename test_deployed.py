import argparse
import os
import vertexai
from dotenv import load_dotenv
from vertexai.preview import reasoning_engines

load_dotenv()
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]

# Resource Name from the latest deployment of the Multi-Agent ADK App
RESOURCE_NAME = "projects/642619647576/locations/europe-west1/reasoningEngines/4577671526710509568"

TEST_QUERIES = [
    "How is the US stock market doing today? Tell me about top tech stocks.",
    # "Can you do both? Give me a brief market summary and then summarize the news.",
]


def parse_chunks(remote_agent, query: str):
    """Yields (is_system_event, text) tuples from the stream."""
    for chunk in remote_agent.stream_query(user_id="test-user", message=query):
        if not isinstance(chunk, dict):
            continue
        author = chunk.get("author", "?")
        actions = chunk.get("actions", {})
        content = chunk.get("content", {})
        parts = content.get("parts", []) if content else []
        
        # Agent transfer
        if actions.get("transfer_to_agent"):
            yield True, f"🔄 [{author}] → [{actions['transfer_to_agent']}]"
        
        for part in parts:
            if "function_call" in part:
                fc = part["function_call"]
                yield True, f"🛠️  [{author}] calling → {fc['name']}({fc.get('args', {})})"
            elif "function_response" in part:
                fr = part["function_response"]
                result = str(fr.get("response", {}).get("result", ""))
                snippet = result[:150].replace("\n", " ") + ("..." if len(result) > 150 else "")
                yield True, f"📦 [{author}] result → {snippet}"
            elif "text" in part and part["text"]:
                yield False, part["text"]
            elif chunk.get("error_message"):
                yield True, f"❌ [{author}] error → {chunk['error_message']}"


def test_stream(remote_agent):
    """Shows streaming output with debug events."""
    print("Mode: stream (real-time with debug events)\n")
    for query in TEST_QUERIES:
        print(f"{'='*60}\nQuery: {query}\n{'='*60}")
        print("[Debug Events]:")
        final_text = ""
        for is_system, text in parse_chunks(remote_agent, query):
            if is_system:
                print(f"  {text}")
            else:
                final_text = text
        print(f"\n[Agent Final Output]\n{final_text}\n")


def test_sync(remote_agent):
    """Collects stream and prints only the final text (no debug events)."""
    print("Mode: sync (collect stream, show final output only)\n")
    for query in TEST_QUERIES:
        print(f"{'='*60}\nQuery: {query}\n{'='*60}")
        final_text = ""
        for is_system, text in parse_chunks(remote_agent, query):
            if not is_system:
                final_text = text  # keep the latest text chunk
        print(f"\n{final_text}\n")


def main():
    parser = argparse.ArgumentParser(description="Test the deployed Multi-Agent Orchestrator.")
    parser.add_argument(
        "--mode",
        choices=["stream", "sync"],
        default="sync",
        help="'stream' = show debug events + final output, 'sync' = final output only (default: sync)"
    )
    args = parser.parse_args()

    print(f"=== Testing Deployed Multi-Agent Orchestrator ===\n")
    vertexai.init(project=PROJECT_ID, location=LOCATION)
    remote_agent = reasoning_engines.ReasoningEngine(RESOURCE_NAME)

    try:
        if args.mode == "stream":
            test_stream(remote_agent)
        else:
            test_sync(remote_agent)
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
