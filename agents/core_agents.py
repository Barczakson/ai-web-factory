from crewai import Agent, Task
from crewai_tools import FileReadTool, WebsiteSearchTool # Removed FileWriterTool
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import time
from supabase import create_client, Client
from utils import get_secret # Import get_secret from utils

# Usunięto zduplikowaną funkcję get_secret, teraz importowana z utils.py
# api_key = get_secret('gemini_api_key') # Ta linia nie jest już potrzebna, klucz pobierany w get_llm

class RateLimiter:
    def __init__(self, requests_per_minute=10):
        self.interval = 60 / requests_per_minute
        self.last_request = 0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_request
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_request = time.time()

rate_limiter = RateLimiter()

def get_llm():
    rate_limiter.wait()  # Limit 10 zapytań/minutę
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # Użyj stabilnej wersji, jeśli -2.0 nie działa
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        max_tokens=4096
    )
    return llm

class SupabaseTool:
    """
    This class is currently unused in the main project generation flow.
    Supabase interactions are handled directly using the create_client instance in generate_project.py.
    This tool is kept here for potential future use as a dedicated Supabase interaction tool for agents.
    """
    def __init__(self):
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("BŁĄD: SUPABASE_URL lub SUPABASE_SERVICE_KEY nie są ustawione.")
        self.client: Client = create_client(supabase_url, supabase_key)

    def save_project(self, project_data):
        return self.client.table("project_generations").insert(project_data).execute()

class ProjectPlannerAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21",
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Project Planner",
            goal="Create a detailed project plan based on requirements.",
            backstory="You are an expert project manager with experience in web development.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def create_plan_task(self, project_name, framework, features):
        return Task(
            description=f"Create a project plan for {project_name} using {framework} with features: {features}.",
            agent=self,
            expected_output="A JSON file with project plan details."
        )

class CodeGeneratorAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Code Generator",
            goal="Generate code based on project plan.",
            backstory="You are a senior developer proficient in multiple frameworks.",
            verbose=True,
            allow_delegation=False,
            tools=[], # Usunięto FileWriterTool
            llm=llm
        )

    def create_codegen_task(self, project_name, plan_path):
        return Task(
            description=f"Generate code for {project_name} based on plan: {plan_path}.",
            agent=self,
            expected_output="Generated source code files."
        )

class CodeReviewerAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Code Reviewer",
            goal="Review code for quality and standards.",
            backstory="You are a meticulous code reviewer with a focus on best practices.",
            verbose=True,
            allow_delegation=False,
            tools=[FileReadTool()],
            llm=llm
        )

    def create_review_task(self, code_path):
        return Task(
            description=f"Review code in {code_path} for quality and standards.",
            agent=self,
            expected_output="A report with code review findings."
        )

class TestGeneratorAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Test Generator",
            goal="Generate automated tests for the project.",
            backstory="You are a QA engineer specializing in test automation.",
            verbose=True,
            allow_delegation=False,
            tools=[], # Usunięto FileWriterTool
            llm=llm
        )

    def create_test_task(self, project_path):
        return Task(
            description=f"Generate tests for project in {project_path}.",
            agent=self,
            expected_output="Test files for the project."
        )

class DeploymentAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Deployment Specialist",
            goal="Deploy the project to a hosting platform.",
            backstory="You are a DevOps engineer with expertise in cloud deployments.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def create_deploy_task(self, project_path, project_name):
        return Task(
            description=f"Deploy project {project_name} from {project_path}.",
            agent=self,
            expected_output="Deployment URL and status."
        )

class DatabaseAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Database Manager",
            goal="Manage database schema and migrations.",
            backstory="You are a database administrator with expertise in SQL and NoSQL.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def create_db_task(self, project_name, schema):
        return Task(
            description=f"Create database schema for {project_name}: {schema}.",
            agent=self,
            expected_output="Database schema and migration scripts."
        )

class MonitoringAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Monitoring Specialist",
            goal="Set up monitoring for the project.",
            backstory="You are an expert in observability and monitoring solutions.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def create_monitor_task(self):
        return Task(
            description="Set up monitoring for the project.",
            agent=self,
            expected_output="Monitoring configuration details."
        )

class FeedbackAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Feedback Analyst",
            goal="Collect and analyze feedback for the project.",
            backstory="You are an expert in user feedback analysis.",
            verbose=True,
            allow_delegation=False,
            llm=llm
        )

    def create_feedback_task(self, context):
        return Task(
            description=f"Analyze feedback for: {context}.",
            agent=self,
            expected_output="Feedback analysis report."
        )

class QualityAssuranceAgent(Agent):
    def __init__(self):
        # google_api_key = os.getenv("GOOGLE_API_KEY") # Klucz pobierany w get_llm
        # if not google_api_key: # Walidacja przeniesiona do get_llm
        #     raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        # llm = ChatGoogleGenerativeAI( # Zastąpiono wywołaniem get_llm()
        #     model="gemini-2.0-flash-thinking-exp-01-21",
        #     google_api_key=google_api_key,
        #     temperature=0.7
        # )
        llm = get_llm()

        super().__init__(
            role="Quality Assurance Specialist",
            goal="Ensure code quality, standards compliance, and perform static analysis.",
            backstory="You are a meticulous QA specialist with expertise in code quality tools like SonarQube and linters.",
            verbose=True,
            allow_delegation=False,
            tools=[], # Add relevant tools later if needed, e.g., for running linters or interacting with SonarQube API
            llm=llm
        )

    def create_quality_check_task(self, project_path):
        return Task(
            description=f"Perform quality checks and static analysis on the project in {project_path}.",
            agent=self,
            expected_output="A report detailing code quality issues, linting errors, and suggestions for improvement."
        )