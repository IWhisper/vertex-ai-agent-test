import vertexai
from vertexai.preview import reasoning_engines

# Using the project and location we confirmed works
PROJECT_ID = "project-0685f1f4-a98d-4707-afc"
LOCATION = "europe-west1"

# A Google Cloud Storage bucket is required for deploying Reasoning Engines
# It stores the zipped code and dependencies during the deployment process
STAGING_BUCKET = f"gs://{PROJECT_ID}-agent-staging"

def deploy_agent():
    print("Initializing Vertex AI...")
    vertexai.init(project=PROJECT_ID, location=LOCATION, staging_bucket=STAGING_BUCKET)
    
    print("Deploying Agent Engine instance. This may take a few minutes...")
    
    # 1. Instantiate the agent locally first
    from agent import RssSummarizerAgent
    local_agent = RssSummarizerAgent()
    
    # 2. Deploy it using the object directly
    # We use vertexai.preview.reasoning_engines.ReasoningEngine.create as verified in the SDK
    remote_agent = reasoning_engines.ReasoningEngine.create(
        reasoning_engine=local_agent,
        requirements=[
            "google-cloud-aiplatform[reasoningengine,langchain]>=1.50.0",
            "feedparser>=6.0.11",
            "requests>=2.31.0"
        ],
        extra_packages=["agent.py"],
        display_name="RSS Summarizer Agent",
        description="An agent that fetches RSS/JSON feeds and summarizes them using Gemini",
    )
    
    print("\n✅ Deployment successful!")
    print(f"Agent Resource Name: {remote_agent.resource_name}")
    print("\nTo test the deployed agent later, you can use the SDK with:")
    print(f"reasoning_engines.ReasoningEngine('{remote_agent.resource_name}')")

if __name__ == "__main__":
    deploy_agent()
