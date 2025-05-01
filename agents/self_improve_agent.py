from crewai import Agent, Task
from crewai_tools import FileReadTool
from agents.core_agents import llm # Import shared llm instance

class SelfImproveAgent(Agent):
    def __init__(self):
        super().__init__(
            role="Code Improvement Specialist",
            goal="Analyze and suggest improvements for agent code to enhance performance and maintainability.",
            backstory=(
                "You are an expert in code optimization and software engineering, specializing in Python and AI agent frameworks. "
                "Your mission is to review agent code, identify inefficiencies, and propose actionable improvements using Gemini 2.0 Flash."
            ),
            verbose=True,
            allow_delegation=False,
            llm=llm, # Use the imported shared llm instance
            tools=[FileReadTool()] # Add FileReadTool to the agent's tools
        )

    def create_improve_task(self, code_path):
        """
        Tworzy zadanie poprawy kodu dla podanego pliku.
        Args:
            code_path (str): Ścieżka do pliku z kodem (np. /app/agents/core_agents.py).
        Returns:
            Task: Obiekt zadania dla CrewAI.
        """
        # The agent will use the FileReadTool to read the file content.
        # The task description instructs the agent on what to do with the file.
        task_description = (
            f"Analyze the Python code file located at {code_path}. " # Instruct the agent to use the tool
            "Identify potential issues such as inefficient algorithms, code smells, or maintainability problems. "
            "Suggest specific improvements, including code snippets where applicable. "
            "Provide a concise report with at least 3 actionable suggestions."
        )

        return Task(
            description=task_description,
            agent=self,
            expected_output=(
                "A report containing at least 3 actionable suggestions for improving the code, "
                "including code snippets and explanations."
            )
        )