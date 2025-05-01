from crewai import Agent
from litellm import LiteLLM
import os
from dotenv import load_dotenv
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Ustawienie debugowania LiteLLM
os.environ['LITELLM_LOG'] = 'DEBUG'

load_dotenv()

# Sprawdzenie klucza API
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    logger.error("GEMINI_API_KEY not found in .env")
    raise ValueError("GEMINI_API_KEY is required")

llm = LiteLLM(
    api_key=api_key,
    base_url="https://api.gemini.com/v1",
    timeout=30  # Timeout 30 sekund dla zapytań API
)

# Definicja agentów
code_generator = Agent(
    role="Code Generator",
    goal="Generate high-quality code based on project specifications",
    backstory="Experienced developer with expertise in Next.js and Flask",
    llm=llm,
    verbose=True
)

verifier = Agent(
    role="Code Verifier",
    goal="Verify code quality and compliance with standards",
    backstory="QA engineer with SonarQube expertise",
    llm=llm,
    verbose=True
)

# Placeholder Agents (to resolve import errors in generate_project.py)
class ProjectPlannerAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class CodeReviewerAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class TestGeneratorAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class DeploymentAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class DatabaseAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class SupabaseTool: # Assuming SupabaseTool is not an Agent but a tool class
     pass

class QualityAssuranceAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    def create_quality_check_task(self, project_dir):
        # Placeholder task
        return Task(description="Perform quality check.", agent=self, expected_output="Quality report.")

class MonitoringAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class FeedbackAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)