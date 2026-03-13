import os
import vertexai
from dotenv import load_dotenv

# Load configuration from .env
load_dotenv()
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]

# -------------------------------------------------------------------------------------
# USER ACTION REQUIRED: Replace with your Developer Connect Git Repository Link
# Example: "projects/642619647576/locations/europe-west1/connections/github-conn/gitRepositoryLinks/vertex-ai-agent-test"
# -------------------------------------------------------------------------------------
GIT_REPOSITORY_LINK = os.environ["GIT_REPOSITORY_LINK"]

def deploy_agent_from_github():
    if "YOUR_GIT_REPOSITORY_LINK" in GIT_REPOSITORY_LINK:
        print("❌ Error: Please update GIT_REPOSITORY_LINK in this script first.")
        return

    print(f"Initializing Vertex AI GenAI Client (Project: {PROJECT_ID}, Location: {LOCATION})...")
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)

    print(f"Deploying Agent Engine instance from GitHub ({GIT_REPOSITORY_LINK})...")
    
    # Configuration for Developer Connect deployment
    config = {
        "display_name": "Multi-Agent (GitHub)",
        "description": "Orchestrated multi-agent system deployed from GitHub",
        "developer_connect_source": {
            "git_repository_link": GIT_REPOSITORY_LINK,
            "revision": "main",  # Branch, tag, or commit SHA
            "dir": ".",          # Root directory of the agent code in the repo
        },
        "entrypoint_module": "orchestrator_agent.agent",
        "entrypoint_object": "app",
        "requirements_file": "requirements.txt",
        
        # -------------------------------------------------------------------------------------
        # API METHODS EXPOSURE
        # -------------------------------------------------------------------------------------
        "class_methods": [
            {
                "name": "stream_query",
                "api_mode": "stream",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string", "description": "The user ID."},
                        "message": {"type": "string", "description": "The user request/message."},
                    },
                    "required": ["user_id", "message"],
                    "type": "object"
                }
            },
            {
                "name": "query",
                "api_mode": "",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string", "description": "The user ID."},
                        "message": {"type": "string", "description": "The user request/message."},
                    },
                    "required": ["user_id", "message"],
                    "type": "object"
                }
            },
            {
                "name": "create_session",
                "api_mode": "",
                "parameters": {
                    "properties": {
                        "user_id": {"type": "string", "description": "The user ID."},
                    },
                    "required": ["user_id"],
                    "type": "object"
                }
            },
        ]
    }

    try:
        remote_agent = client.agent_engines.create(config=config)
        print("\n✅ GitHub Deployment triggered successfully!")
        print(f"Agent Resource Name: {remote_agent.api_resource.name}")
        print("\n💡 Note: Cloud build might take a few minutes to complete on the backend.")
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")

if __name__ == "__main__":
    deploy_agent_from_github()
