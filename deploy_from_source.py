import vertexai
from dotenv import load_dotenv
import os

load_dotenv()
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
LOCATION = os.environ["GOOGLE_CLOUD_LOCATION"]

def deploy_agent_from_source():
    print("Initializing Vertex AI GenAI Client...")
    
    # In SDK versions >= 1.141.0, the recommended approach is using the new Client
    client = vertexai.Client(project=PROJECT_ID, location=LOCATION)
    
    print("Deploying Agent Engine instance from source... ")
    
    remote_agent = client.agent_engines.create(
        config={
            "display_name": "Multi-Agent RSS & Market Assistant",
            "description": "An orchestrated multi-agent system deployed from local source.",
            "source_packages": ["."], # Current directory
            "entrypoint_module": "orchestrator_agent.agent", # The module containing `app`
            "entrypoint_object": "app", # The AdkApp object
            "requirements_file": "requirements.txt",
            
            # -------------------------------------------------------------------------------------
            # NOTE ON class_methods:
            # When using `source_packages` deployment, Vertex AI ALWAYS requires explicit `class_methods`
            # so it knows which Python methods to expose as REST endpoints.
            # 
            # For AdkApp, the standard interface is `stream_query` (the async streaming endpoint).
            # We also expose session management methods so callers can manage conversation sessions.
            # -------------------------------------------------------------------------------------
            "class_methods": [
                {
                    "name": "stream_query",
                    "api_mode": "stream",
                    "parameters": {
                        "properties": {
                            "user_id": {"type": "string", "description": "The user ID for the session."},
                            "message": {"type": "string", "description": "The user message to send to the agent."},
                            "session_id": {"type": "string", "description": "Optional existing session ID."},
                        },
                        "required": ["user_id", "message"],
                        "type": "object"
                    }
                },
                {
                    # Non-streaming, blocking endpoint.
                    # Implemented in OrchestratorApp.query() which wraps stream_query().
                    "name": "query",
                    "api_mode": "",  # Empty string = synchronous blocking
                    "parameters": {
                        "properties": {
                            "user_id": {"type": "string", "description": "The user ID for the session."},
                            "message": {"type": "string", "description": "The user message to send to the agent."},
                            "session_id": {"type": "string", "description": "Optional existing session ID."},
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
            ],
        }
    )
    
    print("\n✅ Source Deployment successful!")
    print(f"Agent Resource Name: {remote_agent.api_resource.name}")

if __name__ == "__main__":
    deploy_agent_from_source()
