import argparse
import json
import os
import re
import logging
import time
import requests
import yaml
from dotenv import load_dotenv
from agents.core_agents import ProjectPlannerAgent, CodeGeneratorAgent, CodeReviewerAgent, TestGeneratorAgent, DeploymentAgent, DatabaseAgent, RateLimiter, SupabaseTool, QualityAssuranceAgent, MonitoringAgent, FeedbackAgent # Import necessary agents and tools, including QualityAssuranceAgent
from agents.project_editor_agent import ProjectEditorAgent # Import ProjectEditorAgent
from agents.self_improve_agent import SelfImproveAgent # Import SelfImproveAgent
from crewai import Crew, Process, Agent, Task
from supabase import create_client
from utils import get_secret # Import get_secret from utils

load_dotenv()

# Konfiguracja LiteLLM (dodana w celu rozwiązania błędu "LLM Provider NOT provided")
import litellm
import os

# Ustaw domyślny model i klucz API dla litellm, nawet jeśli agenci używają ChatGoogleGenerativeAI
# Może to zapobiec błędom, jeśli CrewAI/mem0 próbuje użyć litellm wewnętrznie
litellm.set_verbose(True) # Włącz szczegółowe logowanie litellm dla debugowania
litellm.model = "gemini-1.5-flash" # Ustaw domyślny model
litellm.api_key = os.getenv("GOOGLE_API_KEY") # Ustaw domyślny klucz API


# Debugging zmiennych środowiskowych
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY") # Używamy SUPABASE_SERVICE_KEY dla spójności
# print(f"SUPABASE_URL: {supabase_url}") # Komentujemy, żeby nie logować kluczy
# print(f"SUPABASE_SERVICE_KEY: {supabase_key}") # Komentujemy, żeby nie logować kluczy

if not supabase_url or not supabase_key:
    raise ValueError("Brak wymaganych zmiennych: SUPABASE_URL lub SUPABASE_SERVICE_KEY")

supabase = create_client(supabase_url, supabase_key)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Usunięto zduplikowaną funkcję get_secret, teraz importowana z utils.py
api_key = get_secret('gemini_api_key')

def load_config_from_yaml(filepath):
    """Loads configuration from a YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {filepath}")
        return None
    except yaml.YAMLError as e:
        logging.error(f"Error parsing YAML file {filepath}: {e}")
        return None

def create_supabase_table(table_name, schema):
    """
    Creates a table in Supabase with the given schema using the Management API.
    Schema is expected to be a list of column definitions as strings (e.g., ["id UUID PRIMARY KEY", "name TEXT"]).
    This function will attempt to convert this into a format suitable for the Management API.
    NOTE: This conversion might be lossy or incomplete depending on the complexity of the schema strings.
    A more robust solution would involve a structured schema definition from the planning agent.
    """
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_service_key:
        logging.error("SUPABASE_URL or SUPABASE_SERVICE_KEY not set.")
        return {"status": "failure", "message": "Supabase credentials not set."}

    # Extract project_ref from SUPABASE_URL
    try:
        # Assuming SUPABASE_URL is in the format https://<project_ref>.supabase.co
        project_ref = supabase_url.split("//")[1].split(".")[0]
    except IndexError:
        logging.error(f"Could not extract project_ref from SUPABASE_URL: {supabase_url}")
        return {"status": "failure", "message": "Invalid SUPABASE_URL format."}

    # Supabase Management API endpoint for tables
    management_api_url = f"https://api.supabase.com/v1/projects/{project_ref}/tables"

    # Attempt to parse schema strings into a structure for the Management API
    columns_payload = []
    # Regex to capture column name, type, and the rest of the definition
    # Handles quoted identifiers and types with parentheses
    # Updated regex to be more robust
    col_def_pattern = re.compile(r'^[\s]*["`]?([\w]+)["`]?[\s]+([\w\(\),]+)[\s]*(.*)$')

    for col_def in schema:
        col_def = col_def.strip()
        if not col_def:
            continue

        match = col_def_pattern.match(col_def)
        if not match:
            logging.warning(f"Could not parse column definition: {col_def}. Skipping.")
            continue

        col_name = match.group(1)
        col_type = match.group(2).rstrip(',') # Remove trailing comma if any
        constraints_str = match.group(3).strip()

        is_primary_key = "PRIMARY KEY" in constraints_str.upper()
        is_nullable = "NOT NULL" not in constraints_str.upper()
        is_unique = "UNIQUE" in constraints_str.upper()

        # Basic handling for DEFAULT value - needs more robust parsing for complex defaults
        default_value = None
        default_match = re.search(r'DEFAULT\s+(.+)', constraints_str, re.IGNORECASE) # Use IGNORECASE
        if default_match:
             # This is a very basic default value extraction, might need refinement
             default_value = constraints_str[default_match.start(1):].strip()
             # Attempt to remove trailing commas or parentheses if they are part of the constraint syntax
             default_value = re.sub(r'[,;)]+$', '', default_value)


        # Add more parsing logic for other constraints (CHECK, REFERENCES, etc.) if needed
        column_info = {
            "name": col_name,
            "type": col_type,
            "primary_key": is_primary_key,
            "is_nullable": is_nullable,
            "is_unique": is_unique,
            # Supabase Management API might expect default_value as a string or specific type
            # Need to confirm Supabase API spec for default values
            # For now, sending as string if found
        }
        if default_value is not None:
             # Supabase API expects default_value as a string representation
             column_info["default_value"] = default_value

        columns_payload.append(column_info)

    # Add a check if columns_payload is empty after parsing
    if not columns_payload:
        logging.error(f"No valid columns parsed from schema: {schema}. Cannot create table.")
        return {"status": "failure", "message": "No valid columns parsed from schema."}


    payload = {
        "name": table_name,
        "columns": columns_payload,
        # Add other table properties if needed (e.g., schema, comment)
        "schema": "public" # Assuming 'public' schema
    }

    headers = {
        "apikey": supabase_service_key,
        "Authorization": f"Bearer {supabase_service_key}",
        "Content-Type": "application/json"
    }

    logging.info(f"Attempting to create table '{table_name}' via Supabase Management API: {management_api_url}")
    logging.debug(f"Payload: {json.dumps(payload)}")

    try:
        response = requests.post(management_api_url, headers=headers, json=payload)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)

        logging.info(f"Supabase table creation response status: {response.status_code}")
        logging.debug(f"Supabase table creation response body: {response.text}")

        # Check response body for success confirmation if needed
        return {"status": "success", "message": f"Table '{table_name}' created successfully."}

    except requests.exceptions.RequestException as e:
        logging.error(f"Error creating Supabase table '{table_name}': {e}")
        # Attempt to parse error details from response if available
        error_message = str(e)
        response = e.response # Get the response object from the exception
        if response is not None and response.text:
            try:
                error_details = response.json()
                if 'message' in error_details:
                    error_message = error_details['message']
                elif 'error' in error_details:
                     error_message = error_details['error']
                elif 'details' in error_details:
                     error_message = error_details['details']
            except json.JSONDecodeError:
                pass # Ignore if response is not JSON

        return {"status": "failure", "message": f"Failed to create table '{table_name}': {error_message}"}
    except Exception as e:
        logging.error(f"An unexpected error occurred during Supabase table creation for '{table_name}': {e}")
        return {"status": "failure", "message": f"An unexpected error occurred: {str(e)}"}


# Mapping of agent roles to agent classes for dynamic loading
AGENT_CLASS_MAP = {
    'Project Planner': ProjectPlannerAgent,
    'Code Generator': CodeGeneratorAgent,
    'Code Reviewer': CodeReviewerAgent,
    'Test Generator': TestGeneratorAgent,
    'Deployment Specialist': DeploymentAgent,
    'Database Manager': DatabaseAgent,
    'Monitoring Specialist': MonitoringAgent,
    'Feedback Analyst': FeedbackAgent,
    'Quality Assurance Specialist': QualityAssuranceAgent,
    'Project Editor': ProjectEditorAgent,
    'Code Improvement Specialist': SelfImproveAgent,
}

def fetch_and_parse_sonar_results(project_name, sonar_url, sonar_token=None):
    """
    Fetches SonarQube analysis results (issues) for a given project and parses them.
    Assumes SonarQube API is available at sonar_url.
    """
    issues_api_url = f"{sonar_url}/api/issues/search"
    headers = {}
    if sonar_token:
        # Assuming token-based authentication
        headers["Authorization"] = f"Bearer {sonar_token}"

    params = {
        "componentKeys": project_name,
        "types": "CODE_SMELL,BUG,VULNERABILITY,SECURITY_HOTSPOT", # Fetch common issue types
        "ps": 500 # Page size, adjust if needed
    }

    all_issues = []
    page = 1
    while True:
        params["p"] = page
        logging.info(f"Fetching SonarQube issues page {page} for project {project_name} from {issues_api_url}")
        try:
            response = requests.get(issues_api_url, headers=headers, params=params)
            response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
            data = response.json()

            issues = data.get("issues", [])
            all_issues.extend(issues)

            total_issues = data.get("total", 0)
            page_size = data.get("ps", 0)

            if (page * page_size) >= total_issues:
                break # Fetched all pages
            page += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching SonarQube issues: {e}")
            return None
        except json.JSONDecodeError:
            logging.error("Failed to parse SonarQube API response as JSON.")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred while fetching SonarQube issues: {e}")
            return None

    logging.info(f"Successfully fetched {len(all_issues)} issues from SonarQube.")
    return all_issues


def main():
    parser = argparse.ArgumentParser(description="Generate or edit a project.")
    parser.add_argument("--project", required=True, help="Name of the project")
    parser.add_argument("--framework", help="Framework to use (e.g., Next.js, Flask)")
    parser.add_argument("--features", help="Comma-separated list of features (e.g., Uwierzytelnie Supabase, tabela todos)")
    parser.add_argument("--edit", action="store_true", help="Edit an existing project")
    parser.add_argument("--changes", help="Description of changes to implement")
    parser.add_argument("--config", help="Path to a JSON configuration file") # Dodajemy argument --config
    args = parser.parse_args()

    try:
        project_name = args.project
        project_dir = os.path.join("projects", project_name) # Zmieniamy na ścieżkę względną
        logging.info(f"Project directory: {project_dir}")

        if not os.path.exists(project_dir):
            logging.warning(f"Project directory {project_dir} does not exist. Creating...")
            os.makedirs(project_dir, exist_ok=True)

        if args.edit:
            if not args.changes:
                raise ValueError("BŁĄD: --changes jest wymagany w trybie edycji.")

            # Load agents and tasks from YAML (assuming agents.yaml and tasks.yaml exist and are correctly formatted)
            agents_config = load_config_from_yaml('ai-web-factory/agents.yaml')
            tasks_config = load_config_from_yaml('ai-web-factory/tasks.yaml')

            if not agents_config or not tasks_config:
                raise Exception("Failed to load agents or tasks configuration from YAML.")

            # Create agents from config using the mapping
            crew_agents = []
            agent_map = {}
            if 'agents' in agents_config:
                for agent_data in agents_config['agents']:
                    agent_role = agent_data.get('role')
                    agent_class = AGENT_CLASS_MAP.get(agent_role)

                    if agent_class:
                         try:
                             # Ensure verbose is True for all agents loaded from YAML unless explicitly set to False
                             agent_data['verbose'] = agent_data.get('verbose', True)
                             # Instantiate agent class dynamically
                             agent = agent_class(**agent_data)
                             crew_agents.append(agent)
                             agent_map[agent_role] = agent
                         except Exception as e:
                             logging.error(f"Error instantiating agent {agent_role} with data {agent_data}: {e}")
                             continue
                         else:
                             logging.warning(f"Unknown agent role or missing class in AGENT_CLASS_MAP for agent: {agent_role}. Skipping agent.")
                             continue


            # Create tasks from config
            crew_tasks = []
            if 'tasks' in tasks_config:
                for task_data in tasks_config['tasks']:
                    # Find the agent for this task by role
                    task_agent = agent_map.get(task_data.get('agent'))
                    if not task_agent:
                        logging.warning(f"Agent not found for task: {task_data.get('description')}. Skipping task.")
                        continue

                    # Remove the 'agent' key as it's passed separately
                    task_data.pop('agent', None)

                    task = Task(**task_data, agent=task_agent)
                    crew_tasks.append(task)

            if not crew_agents or not crew_tasks:
                 raise Exception("No agents or tasks were successfully loaded from YAML.")

            crew = Crew(
                agents=crew_agents,
                tasks=crew_tasks,
                process=Process.sequential,
                verbose=True, # Keep crew verbose logging
                max_rpm=10, # Ujednolicono max_rpm na 10
                max_iterations=50
            )

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    result = crew.kickoff()
                    logging.debug(f"Edit task result (raw): {result}")
                    break
                except Exception as e:
                    if "ResourceExhausted" in str(e):
                        logging.warning(f"Gemini API quota exceeded. Waiting 60 seconds before retry {attempt + 1}/{max_attempts}...")
                        time.sleep(60)
                    else:
                        raise
            else:
                raise Exception("Failed to complete task due to Gemini API quota limits")

            files_to_write = {}
            result_str = str(result)

            debug_path = os.path.join(project_dir, "debug_result.txt") # Zapisujemy debug_result w katalogu projektu
            try:
                with open(debug_path, "w", encoding="utf-8") as f:
                    f.write(result_str)
                logging.info(f"Saved raw result to {debug_path} for debugging")
            except Exception as e:
                logging.error(f"Failed to write debug_result.txt: {str(e)}")

            # Parsowanie formatu "--- <ścieżka_pliku> ---"
            file_pattern = r'---\s*(\S+?)\s*---\s*(.*?)(?=(---|\Z))'
            file_matches = re.finditer(file_pattern, result_str, re.DOTALL)
            for match in file_matches:
                file_name = match.group(1).strip()
                file_content = match.group(2).strip()
                files_to_write[file_name] = file_content
                logging.info(f"Parsed content for {file_name}:\n{file_content[:100]}...")

            # Parsowanie formatu "**File: /app/SupabaseToDo/<filename>**" jako fallback (dostosowane do dynamicznej nazwy projektu)
            file_pattern_fallback = r'\*\*File: /app/' + re.escape(project_name) + r'/(\S+?)\*\*\s*```(?:html|css|javascript|python)?\s*(.*?)\s*```'
            file_matches_fallback = re.finditer(file_pattern_fallback, result_str, re.DOTALL)
            for match in file_matches_fallback:
                file_name = match.group(1)
                file_content = match.group(2).strip()
                files_to_write[file_name] = file_content
                logging.info(f"Parsed fallback content for {file_name}:\n{file_content[:100]}...")


            if not files_to_write:
                logging.warning("No files parsed from agent output. Check result format and debug_result.txt.")
            else:
                for file_name, content in files_to_write.items():
                    file_path = os.path.join(project_dir, file_name)
                    try:
                        # Ensure parent directories exist
                        os.makedirs(os.path.dirname(file_path), exist_ok=True)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(content) # Corrected: removed duplicate f.write
                        logging.info(f"Manually written file: {file_path}")
                    except Exception as e:
                        logging.error(f"Failed to write file {file_path}: {str(e)}")


            print(json.dumps({
                "status": "success",
                "project_name": project_name,
                "features": args.changes, # W trybie edycji features to args.changes
                "deployment_url": "" # URL wdrożenia nie jest jeszcze znany po edycji
            }))

            # Dodaj kod do wywołania webhooka n8n
            n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
            if n8n_webhook_url:
                data_to_send = {"projectName": project_name, "changes": args.changes, "status": "edited"}

                try:
                    logging.info(f"Wywoływanie webhooka n8n pod adresem: {n8n_webhook_url}")
                    response = requests.post(n8n_webhook_url, json=data_to_send)
                    response.raise_for_status() # Zgłoś wyjątek dla błędnych statusów (4xx lub 5xx)
                    logging.info(f"Webhook n8n wywołany pomyślnie. Status: {response.status_code}")
                    logging.debug(f"Odpowiedź webhooka: {response.text}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"Błąd podczas wywoływania webhooka n8n: {e}")
            else:
                logging.warning("N8N_WEBHOOK_URL nie jest ustawiony w .env. Pomijam wywołanie webhooka.")


        else: # Tryb generowania projektu
            if not args.framework or not args.features:
                 # Sprawdź, czy podano --config
                 if args.config:
                     config_data = load_config_from_yaml(args.config)
                     if config_data:
                         args.framework = config_data.get('framework')
                         args.features = config_data.get('features')
                         # Możesz dodać obsługę innych pól z pliku konfiguracyjnego, np. 'project_name'
                         if not args.project and config_data.get('project_name'):
                             args.project = config_data.get('project_name')
                             project_name = args.project
                             project_dir = os.path.join("projects", project_name)
                             if not os.path.exists(project_dir):
                                 os.makedirs(project_dir, exist_ok=True)
                             logging.info(f"Project name updated from config: {project_name}")

                     if not args.framework or not args.features:
                         raise ValueError("BŁĄD: Plik konfiguracyjny musi zawierać 'framework' i 'features'.")
                 else:
                     raise ValueError("BŁĄD: W trybie generowania wymagane są argumenty --framework i --features lub --config.")


            logging.info(f"Rozpoczynanie generowania projektu: {project_name} ({args.framework}) z funkcjami: {args.features}")

            # ETAP 1: Inicjalizacja projektu (częściowo zrobione powyżej)
            # Tutaj można dodać logikę zapisu do bazy danych o rozpoczęciu generowania
            try:
                insert_result = supabase.table("project_generations").insert({
                    "project_name": project_name,
                    "framework": args.framework,
                    "features": args.features,
                    "start_time": "now()", # Użyj funkcji bazy danych do ustawienia czasu
                    "status": "In Progress"
                }).execute()
                # Sprawdź, czy wstawienie się powiodło
                if insert_result.data:
                    logging.info(f"Zapisano rozpoczęcie generowania projektu do Supabase: {insert_result.data}")
                else:
                     logging.warning(f"Nie udało się zapisać rozpoczęcia generowania projektu do Supabase: {insert_result.error}")
            except Exception as e:
                 logging.error(f"Błąd podczas zapisu rozpoczęcia generowania do Supabase: {e}")


            # Inicjalizacja agentów
            # Using the AGENT_CLASS_MAP for instantiation
            planner_agent = AGENT_CLASS_MAP['Project Planner']()
            db_agent = AGENT_CLASS_MAP['Database Manager']()
            codegen_agent = AGENT_CLASS_MAP['Code Generator']()
            reviewer_agent = AGENT_CLASS_MAP['Code Reviewer']()
            test_agent = AGENT_CLASS_MAP['Test Generator']()
            deployment_agent = AGENT_CLASS_MAP['Deployment Specialist']()
            quality_agent = AGENT_CLASS_MAP['Quality Assurance Specialist']()
            self_improve_agent = AGENT_CLASS_MAP['Code Improvement Specialist']() # Instantiate SelfImproveAgent
            # No need to instantiate RateLimiter here as it's not used for CrewAI limiting


            # ETAP 2: Generowanie kodu z Supabase
            logging.info("ETAP 2: Generowanie kodu z Supabase")

            # Task planowania
            plan_task = Task(
                description=f"Stwórz szczegółowy plan wdrożenia dla projektu {project_name} używając frameworku {args.framework} z funkcjami: {args.features}. Plan powinien zawierać strukturę plików, wymagane tabele Supabase (nazwy i kolumny), oraz kluczowe komponenty do zaimplementowania.",
                agent=planner_agent,
                expected_output="Szczegółowy plan w formacie JSON, zawierający klucze: 'file_structure', 'supabase_tables' (lista obiektów z 'name' i 'schema'), 'components'."
            )

            # Uruchomienie Crew dla planowania
            planning_crew = Crew(
                agents=[planner_agent],
                tasks=[plan_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=10 # Ujednolicono max_rpm na 10
            )

            try:
                planning_result = planning_crew.kickoff()
                logging.debug(f"Planning result: {planning_result}")

                # Parsowanie planu
                try:
                    plan_data = json.loads(planning_result)
                    supabase_tables_schema = plan_data.get('supabase_tables', [])
                    file_structure_plan = plan_data.get('file_structure', {})
                    components_plan = plan_data.get('components', [])

                    # ETAP 2.d: Tworzenie tabel w Supabase
                    logging.info("ETAP 2.d: Tworzenie tabel w Supabase")
                    for table_info in supabase_tables_schema:
                        table_name = table_info.get('name')
                        # Schema is expected as a list of strings, e.g., ["id UUID PRIMARY KEY", "name TEXT"]
                        table_schema = table_info.get('schema')
                        if table_name and table_schema and isinstance(table_schema, list):
                            db_creation_result = create_supabase_table(table_name, table_schema)
                            logging.info(f"Rezultat tworzenia tabeli {table_name}: {db_creation_result}")
                        else:
                            logging.warning(f"Niekompletne lub nieprawidłowe dane dla tabeli Supabase w planie: {table_info}. Oczekiwano 'name' (string) i 'schema' (list of strings).")


                except json.JSONDecodeError:
                    logging.error("Nie udało się sparsować wyniku planowania jako JSON.")
                    supabase_tables_schema = []
                    file_structure_plan = {}
                    components_plan = []
                except Exception as e:
                    logging.error(f"Błąd podczas przetwarzania planu: {e}")
                    supabase_tables_schema = []
                    file_structure_plan = {}
                    components_plan = []


            except Exception as e:
                logging.error(f"Błąd podczas planowania projektu: {e}")
                raise # Przerwij, jeśli planowanie się nie powiedzie

            # Task generowania kodu
            codegen_task = Task(
                description=f"""
                Wygeneruj pełny kod źródłowy dla projektu {project_name} używając frameworku {args.framework} z funkcjami: {args.features}.
                Uwzględnij integrację z Supabase zgodnie z planem.
                Struktura plików powinna być zgodna z planem: {file_structure_plan}.
                Zaimplementuj następujące komponenty: {components_plan}.
                Użyj kluczy Supabase z zmiennych środowiskowych (SUPABASE_URL, SUPABASE_SERVICE_KEY).
                Zwróć pełną zawartość każdego wygenerowanego pliku w formacie:
                --- <ścieżka_pliku_względem_katalogu_projektu> ---
                <zawartość>
                Na przykład:
                --- src/pages/index.js ---
                // kod JavaScript
                --- styles/global.css ---
                /* kod CSS */
                Upewnij się, że ścieżki plików są poprawne i znajdują się w katalogu projektu '{project_dir}'.
                """,
                agent=codegen_agent,
                expected_output="Pełna zawartość wszystkich wygenerowanych plików w formacie '--- <ścieżka_pliku> --- <zawartość>'"
            )

            # Uruchomienie Crew dla generowania kodu
            codegen_crew = Crew(
                agents=[codegen_agent],
                tasks=[codegen_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=10 # Ujednolicono max_rpm na 10
            )

            try:
                codegen_result = codegen_crew.kickoff()
                logging.debug(f"Codegen result: {codegen_result}")

                # Parsowanie i zapisywanie wygenerowanych plików
                files_to_write = {}
                result_str = str(codegen_result)

                # Parsowanie formatu "--- <ścieżka_pliku> ---"
                file_pattern = r'---\s*(\S+?)\s*---\s*(.*?)(?=(---|\Z))'
                file_matches = re.finditer(file_pattern, result_str, re.DOTALL)
                for match in file_matches:
                    file_name = match.group(1).strip()
                    file_content = match.group(2).strip()
                    files_to_write[file_name] = file_content
                    logging.info(f"Parsed content for {file_name}:\n{file_content[:100]}...")

                if not files_to_write:
                    logging.warning("No files parsed from code generation agent output.")
                else:
                    for file_name, content in files_to_write.items():
                        file_path = os.path.join(project_dir, file_name)
                        try:
                            # Ensure parent directories exist
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            logging.info(f"Manually written generated file: {file_path}")
                        except Exception as e:
                            logging.error(f"Failed to write generated file {file_path}: {str(e)}")

            except Exception as e:
                logging.error(f"Błąd podczas generowania kodu: {e}")
                raise # Przerwij, jeśli generowanie kodu się nie powiedzie


            # ETAP 3: Weryfikacja kodu (A2A)
            logging.info("ETAP 3: Weryfikacja kodu (A2A)")
            # Task weryfikacji kodu
            review_task = Task(
                description=f"""
                Przejrzyj kod źródłowy projektu {project_name} znajdujący się w katalogu '{project_dir}'.
                Sprawdź kod pod kątem błędów, zgodności z najlepszymi praktykami dla frameworku {args.framework} i integracji z Supabase.
                Zasugeruj konkretne poprawki, jeśli są potrzebne.
                Zwróć raport z weryfikacji. Jeśli znaleziono błędy, zasugeruj jak je poprawić, podając zmienione fragmenty kodu w formacie:
                --- <ścieżka_pliku_względem_katalogu_projektu> ---
                <poprawiona_zawartość>
                """,
                agent=reviewer_agent,
                expected_output="Raport z weryfikacji kodu. Jeśli znaleziono błędy, poprawione fragmenty kodu w formacie '--- <ścieżka_pliku> --- <poprawiona_zawartość>'"
            )

            # Uruchomienie Crew dla weryfikacji
            review_crew = Crew(
                agents=[reviewer_agent],
                tasks=[review_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=10 # Ujednolicono max_rpm na 10
            )

            try:
                review_result = review_crew.kickoff()
                logging.debug(f"Review result: {review_result}")

                # Parsowanie i zapisywanie poprawionych plików (jeśli agent zwrócił poprawki)
                files_to_write_after_review = {}
                review_result_str = str(review_result)

                file_pattern_review = r'---\s*(\S+?)\s*---\s*(.*?)(?=(---|\Z))'
                file_matches_review = re.finditer(file_pattern_review, review_result_str, re.DOTALL)
                for match in file_matches_review:
                    file_name = match.group(1).strip()
                    file_content = match.group(2).strip()
                    files_to_write_after_review[file_name] = file_content
                    logging.info(f"Parsed corrected content for {file_name} after review:\n{file_content[:100]}...")

                if files_to_write_after_review:
                    logging.info("Applying corrections suggested by the reviewer agent.")
                    for file_name, content in files_to_write_after_review.items():
                        file_path = os.path.join(project_dir, file_name)
                        try:
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            logging.info(f"Manually written corrected file: {file_path}")
                        except Exception as e:
                            logging.error(f"Failed to write corrected file {file_path}: {str(e)}")
                else:
                    logging.info("Reviewer agent did not suggest any code corrections.")


            except Exception as e:
                logging.error(f"Błąd podczas weryfikacji kodu: {e}")
                # Nie przerywamy, błędy w weryfikacji mogą być normalne i mogą być naprawione później


            # ETAP 4: Analiza jakości (A2A) i SonarQube
            logging.info("ETAP 4: Analiza jakości (A2A) i SonarQube")
            # Task analizy jakości
            quality_check_task = quality_agent.create_quality_check_task(project_dir)

            # Uruchomienie Crew dla analizy jakości
            quality_crew = Crew(
                agents=[quality_agent],
                tasks=[quality_check_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=10
            )

            try:
                quality_result = quality_crew.kickoff()
                logging.debug(f"Quality analysis result (from agent): {quality_result}")
                # Process quality analysis result if needed

                # --- SonarQube Integration ---
                logging.info("Uruchamianie skanowania SonarQube...")
                # The sonar-scanner command was executed in the previous step (implicitly by quality_agent).
                # Now, we need to fetch and process the results.

                sonar_url = os.getenv("SONARQUBE_URL")
                sonar_token = os.getenv("SONARQUBE_TOKEN") # Assuming token is stored in env var

                if not sonar_url:
                     logging.warning("SONARQUBE_URL not set in environment variables. Skipping SonarQube integration.")
                     sonar_results_data = None
                else:
                     # Fetch SonarQube analysis results via API
                     sonar_results_data = fetch_and_parse_sonar_results(project_name, sonar_url, sonar_token)


                if sonar_results_data:
                    # Implement logic to parse SonarQube analysis results
                    # The fetch_and_parse_sonar_results function already returns parsed issues (list of dicts)
                    parsed_issues = sonar_results_data # Renaming for clarity

                    if parsed_issues:
                        logging.info(f"Znaleziono {len(parsed_issues)} problemów w analizie SonarQube.")
                        # Implement logic to use SonarQube results for automatic code fixes
                        # This involves feeding the parsed issues to the SelfImproveAgent.

                        logging.info("Applying automatic fixes based on SonarQube results using SelfImproveAgent...")

                        # Create tasks for SelfImproveAgent for each issue or a batch of issues
                        # Assuming SelfImproveAgent has a method like `create_improve_task` or can handle a list of issues
                        # Let's assume SelfImproveAgent can take a list of issues and the project directory
                        fix_task = self_improve_agent.create_improve_task(project_dir, parsed_issues) # Assuming this method exists

                        fix_crew = Crew(
                            agents=[self_improve_agent],
                            tasks=[fix_task],
                            process=Process.sequential,
                            verbose=True,
                            max_rpm=10
                        )

                        logging.info("Running SelfImproveAgent to fix SonarQube issues...")
                        fix_result = fix_crew.kickoff()
                        logging.debug(f"SelfImproveAgent fix result: {fix_result}")

                        # After attempting fixes, you might need to re-run the SonarQube scan
                        # and repeat the parsing/fixing loop until issues are resolved or a limit is reached.
                        # This iterative fixing loop is more complex and might require a separate function or structure.
                        # For now, we'll do one pass of fixing.
                        logging.info("Placeholder: Implement iterative fixing loop and re-scanning.")

                    else:
                        logging.info("Analiza SonarQube nie wykazała żadnych problemów.")
                else:
                    logging.warning("Nie udało się pobrać lub sparsować wyników analizy SonarQube. Sprawdź konfigurację SonarQube i dostępność API.")

                # --- End SonarQube Integration ---

            except Exception as e:
                logging.error(f"Błąd podczas analizy jakości kodu lub przetwarzania wyników SonarQube: {e}")
                # Do not break, quality issues can be addressed later


            # ETAP 5: Testy automatyczne
            logging.info("ETAP 5: Testy automatyczne")
            # Task generowania testów
            test_gen_task = Task(
                description=f"""
                Wygeneruj automatyczne testy dla projektu {project_name} w katalogu '{project_dir}'.
                Użyj odpowiednich narzędzi testowych dla frameworku {args.framework} (np. Playwright dla Next.js, pytest dla Flask).
                Testy powinny pokrywać kluczowe funkcje, w tym integrację z Supabase (np. CRUD, uwierzytelnianie).
                Zwróć pełną zawartość plików testowych w formacie:
                --- <ścieżka_pliku_testowego_względem_katalogu_projektu> ---
                <zawartość>
                """,
                agent=test_agent,
                expected_output="Pełna zawartość wygenerowanych plików testowych w formacie '--- <ścieżka_pliku> --- <zawartość>'"
            )

            # Uruchomienie Crew dla generowania testów
            test_gen_crew = Crew(
                agents=[test_agent],
                tasks=[test_gen_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=10 # Ujednolicono max_rpm na 10
            )

            try:
                test_gen_result = test_gen_crew.kickoff()
                logging.debug(f"Test generation result: {test_gen_result}")

                # Parsowanie i zapisywanie wygenerowanych plików testowych
                files_to_write_tests = {}
                test_gen_result_str = str(test_gen_result)

                file_pattern_tests = r'---\s*(\S+?)\s*---\s*(.*?)(?=(---|\Z))'
                file_matches_tests = re.finditer(file_pattern_tests, test_gen_result_str, re.DOTALL)
                for match in file_matches_tests:
                    file_name = match.group(1).strip()
                    file_content = match.group(2).strip()
                    files_to_write_tests[file_name] = file_content
                    logging.info(f"Parsed generated test content for {file_name}:\n{file_content[:100]}...")

                if not files_to_write_tests:
                    logging.warning("No test files parsed from test generation agent output.")
                else:
                    for file_name, content in files_to_write_tests.items():
                        file_path = os.path.join(project_dir, file_name)
                        try:
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            logging.info(f"Manually written generated test file: {file_path}")
                        except Exception as e:
                            logging.error(f"Failed to write generated test file {file_path}: {str(e)}")

                # Uruchomienie testów (przykład dla Next.js z Playwright/Jest)
                logging.info("Uruchamianie testów automatycznych...")
                test_command = None
                if args.framework == "Next.js":
                    # Zakładamy, że testy są skonfigurowane do uruchomienia np. przez 'npm test' lub 'npx playwright test'
                    test_command = f"cd {project_dir} && npm install && npm test" # Dodajemy npm install przed testami
                elif args.framework == "Flask":
                    # Zakładamy, że testy są skonfigurowane do uruchomienia np. przez 'pytest'
                    test_command = f"cd {project_dir} && pip install -r requirements.txt && pytest" # Dodajemy pip install
                # Dodaj obsługę innych frameworków

                if test_command:
                    logging.info(f"Wykonuję komendę testową: {test_command}")
                    # Rzeczywiste wykonanie komendy testowej
                    # Używamy narzędzia execute_command
                    print(f"<execute_command>\n<command>{test_command}</command>\n</execute_command>")
                else:
                    logging.warning(f"Brak zdefiniowanej komendy testowej dla frameworku: {args.framework}")


            except Exception as e:
                logging.error(f"Błąd podczas generowania lub uruchamiania testów: {e}")
                # Nie przerywamy, błędy w testach mogą być normalne i mogą być naprawione później


            # ETAP 6: Przygotowanie do wdrożenia
            logging.info("ETAP 6: Przygotowanie do wdrożenia")
            # Task przygotowania do wdrożenia (np. generowanie plików konfiguracyjnych)
            deploy_prep_task = Task(
                description=f"""
                Przygotuj projekt {project_name} w katalogu '{project_dir}' do wdrożenia na platformie hostingowej (np. Vercel dla Next.js, Render dla Flask).
                Wygeneruj niezbędne pliki konfiguracyjne (np. vercel.json, render.yaml) i instrukcje wdrożenia (INSTRUCTIONS.md).
                Upewnij się, że konfiguracja uwzględnia zmienne środowiskowe Supabase (SUPABASE_URL, SUPABASE_SERVICE_KEY).
                Zwróć pełną zawartość wygenerowanych plików konfiguracyjnych i instrukcji w formacie:
                --- <ścieżka_pliku_względem_katalogu_projektu> ---
                <zawartość>
                """,
                agent=deployment_agent,
                expected_output="Pełna zawartość wygenerowanych plików konfiguracyjnych i instrukcji w formacie '--- <ścieżka_pliku> --- <zawartość>'"
            )

            # Uruchomienie Crew dla przygotowania do wdrożenia
            deploy_prep_crew = Crew(
                agents=[deployment_agent],
                tasks=[deploy_prep_task],
                process=Process.sequential,
                verbose=True,
                max_rpm=10 # Ujednolicono max_rpm na 10
            )

            try:
                deploy_prep_result = deploy_prep_crew.kickoff()
                logging.debug(f"Deployment preparation result: {deploy_prep_result}")

                # Parsowanie i zapisywanie wygenerowanych plików konfiguracyjnych i instrukcji
                files_to_write_deploy = {}
                deploy_prep_result_str = str(deploy_prep_result)

                file_pattern_deploy = r'---\s*(\S+?)\s*---\s*(.*?)(?=(---|\Z))'
                file_matches_deploy = re.finditer(file_pattern_deploy, deploy_prep_result_str, re.DOTALL)
                for match in file_matches_deploy:
                    file_name = match.group(1).strip()
                    file_content = match.group(2).strip()
                    files_to_write_deploy[file_name] = file_content
                    logging.info(f"Parsed generated deployment content for {file_name}:\n{file_content[:100]}...")

                if not files_to_write_deploy:
                    logging.warning("No deployment preparation files parsed from agent output.")
                else:
                    for file_name, content in files_to_write_deploy.items():
                        file_path = os.path.join(project_dir, file_name)
                        try:
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            logging.info(f"Manually written generated deployment file: {file_path}")
                        except Exception as e:
                            logging.error(f"Failed to write generated deployment file {file_path}: {str(e)}")

                # Rzeczywiste wykonanie Git push i wdrożenia
                logging.info("Wykonuję Git push i wdrożenie...")
                # Używamy narzędzia execute_command
                git_commands = f"cd {project_dir} && git init && git add . && git commit -m \"Initial commit\""
                logging.info(f"Wykonuję komendy Git: {git_commands}")
                print(f"<execute_command>\n<command>{git_commands}</command>\n</execute_command>")

                deploy_command = None
                if args.framework == "Next.js":
                    deploy_command = f"cd {project_dir} && vercel --prod"
                elif args.framework == "Flask":
                    # Przykład dla Render, może wymagać render.yaml i odpowiedniej konfiguracji
                    deploy_command = f"cd {project_dir} && render deploy"
                # Dodaj obsługę innych frameworków

                if deploy_command:
                    logging.info(f"Wykonuję komendę wdrożenia: {deploy_command}")
                    # execute_command tool call would go here
                    print(f"<execute_command>\n<command>{deploy_command}</command>\n</execute_command>")
                    # The deployment URL needs to be parsed from the output of the vercel/render command.
                    # This requires further implementation to capture and parse the command output.
                    deployment_url = "URL_PO_WDROZENIU_DO_PARSOWANIA" # Placeholder indicating need for parsing
                else:
                    logging.warning(f"Brak zdefiniowanej komendy wdrożenia dla frameworku: {args.framework}")
                    deployment_url = "N/A"


                # Zapisanie URL wdrożenia w bazie danych
                try:
                    update_result = supabase.table("project_generations").update({
                        "deployment_url": deployment_url,
                        "status": "Deployed",
                        "end_time": "now()" # Użyj funkcji bazy danych do ustawienia czasu
                    }).eq("project_name", project_name).execute()
                    if update_result.data:
                        logging.info(f"Zaktualizowano URL wdrożenia w Supabase: {update_result.data}")
                    else:
                        logging.warning(f"Nie udało się zaktualizować URL wdrożenia w Supabase: {update_result.error}")
                except Exception as db_error:
                    logging.error(f"Błąd podczas zapisu URL wdrożenia w Supabase: {db_error}")

            except Exception as e:
                logging.error(f"Błąd podczas przygotowania do wdrożenia: {e}")
                # Nie przerywamy, błędy we wdrożeniu mogą być normalne


            # Po zakończeniu wszystkich etapów (lub próbie ich wykonania)
            print(json.dumps({
                "status": "generation_attempt_finished",
                "project_name": project_name,
                "framework": args.framework,
                "features": args.features,
                "deployment_url": deployment_url if 'deployment_url' in locals() else "N/A" # Zwracamy URL jeśli dostępny
            }))

            # Dodaj kod do wywołania webhooka n8n informującego o zakończeniu generowania
            n8n_webhook_url = os.getenv("N8N_WEBHOOK_URL")
            if n8n_webhook_url:
                data_to_send = {
                    "projectName": project_name,
                    "framework": args.framework,
                    "features": args.features,
                    "status": "generation_completed",
                    "deploymentUrl": deployment_url if 'deployment_url' in locals() else "N/A"
                }
                try:
                    logging.info(f"Wywoływanie webhooka n8n (zakończenie generowania) pod adresem: {n8n_webhook_url}")
                    response = requests.post(n8n_webhook_url, json=data_to_send)
                    response.raise_for_status()
                    logging.info(f"Webhook n8n (zakończenie generowania) wywołany pomyślnie. Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    logging.error(f"Błąd podczas wywoływania webhooka n8n (zakończenie generowania): {e}")
            else:
                logging.warning("N8N_WEBHOOK_URL nie jest ustawiony w .env. Pomijam wywołanie webhooka o zakończeniu generowania.")


    except Exception as e:
        logging.error(f"BŁĄD KRYTYCZNY: {str(e)}")
        print(json.dumps({"status": "failure", "message": str(e)}))
        # W przypadku błędu krytycznego, spróbuj zaktualizować status w bazie danych
        try:
            update_result = supabase.table("project_generations").update({
                "status": "Failed",
                "end_time": "now()",
                "notes": f"Critical Error: {str(e)}"
            }).eq("project_name", project_name).execute()
            if update_result.data:
                logging.info(f"Zaktualizowano status błędu w Supabase: {update_result.data}")
            else:
                logging.warning(f"Nie udało się zaktualizować statusu błędu w Supabase: {update_result.error}")
        except Exception as db_error:
            logging.error(f"Błąd podczas zapisu błędu do Supabase: {db_error}")

        raise # Ponownie zgłoś wyjątek, aby proces nadrzędny mógł go obsłużyć


if __name__ == "__main__":
    main()
    # Usunięto test połączenia z Supabase, ponieważ nie jest potrzebny w tym miejscu.

    # Dodaj pętlę, aby utrzymać kontener przy życiu
    print("Skrypt zakończył główne zadanie. Utrzymywanie procesu przy życiu...")
    while True:
        time.sleep(3600) # Czekaj godzinę, aby nie obciążać CPU