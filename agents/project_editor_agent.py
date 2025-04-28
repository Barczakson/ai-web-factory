from crewai import Agent, Task
from langchain_google_genai import ChatGoogleGenerativeAI # Import ChatGoogleGenerativeAI
import os
from utils import get_secret # Import get_secret from utils

# Usunięto zduplikowaną funkcję get_secret, teraz importowana z utils.py
api_key = get_secret('gemini_api_key')

class ProjectEditorAgent(Agent): # Inherit directly from Agent
    def __init__(self, **kwargs): # Accept kwargs for potential future config from YAML
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("BŁĄD: GOOGLE_API_KEY nie jest ustawiony.")

        llm = ChatGoogleGenerativeAI(
            model="gemini/gemini-2.0-flash-thinking-exp-01-21", # Ujednolicono nazwę modelu
            google_api_key=google_api_key,
            temperature=0.7
        )

        super().__init__(
            role='Project Editor',
            goal='Edit project files to implement requested changes',
            backstory='Expert in web development and file management.',
            verbose=kwargs.get('verbose', True), # Allow verbose to be set from kwargs
            allow_delegation=kwargs.get('allow_delegation', False), # Allow delegation to be set from kwargs
            llm=llm,
            **kwargs # Pass remaining kwargs to the parent Agent class
        )

    def create_edit_task(self, project_name, changes):
        task_description = f"""
        Edit project {project_name} in directory /app/{project_name} to implement changes: {changes}.
        If project files (e.g., index.html, style.css, script.js) do not exist, create them with a basic structure.
        Do NOT use FileWriterTool due to persistent errors. Instead, return the full content of each modified file in the following format:
        --- <filename> ---
        <content>
        For example:
        --- index.html ---
        <!DOCTYPE html>
        <html>
        <body><h1>Test</h1></body>
        </html>
        Provide content for all modified files (index.html, style.css, script.js) to implement the changes.
        """
        return Task(
            description=task_description,
            agent=self, # Use self as the agent instance
            expected_output="File contents in --- <filename> --- format for all modified files"
        )