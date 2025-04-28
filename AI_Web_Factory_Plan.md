# Zaktualizowany plan wdrożenia systemu AI Web Factory

**Cel projektu**
AI Web Factory to system automatycznego generowania, edycji, testowania, wdrażania i zarządzania aplikacjami webowymi, oparty na 9 agentach AI (CrewAI), sterowany przez CLI (generate_project.py). Wykorzystuje Supabase jako backend, GitHub do wersjonowania, Vercel do wdrożeń, n8n do automatyzacji, oraz SonarQube do analizy kodu. System samodzielnie instaluje zależności i przygotowuje stanowisko developerskie dla każdego projektu, zapewniając łatwe uruchamianie, obsługę i przekazywanie projektów klientom.

**Wymagania**
Sprzętowe
* System: Windows 11
* GPU: RTX 4060 Ti 16 GB
* RAM: 32 GB
* CPU: 6–8 rdzeni (np. Intel i7-13620H, do potwierdzenia)
* Dysk: SSD 512 GB–1 TB


Oprogramowanie
* Git
* Node.js 18+
* Python 3.11
* Docker Desktop
* Visual Studio Code

Konta i klucze
* Supabase: Projekt (https://jvstwenbkeyewfawsvtc.supabase.co)
* GitHub: Token (GITHUB_TOKEN)
* Vercel: Token (VERCEL_TOKEN)
* Google AI Studio: Klucz Gemini (GOOGLE_API_KEY)
* Discord: Webhook (DISCORD_WEBHOOK_URL)

**Plan wdrożenia krok po kroku**

<!--
<!-- **Krok 1: Przygotowanie repozytorium**
* Cel: Utworzenie lokalnego repozytorium systemu.
* Instrukcje:
    1. Otwórz PowerShell jako administrator.
    2. Utwórz katalog projektu:
       ```powershell
       mkdir C:\GUŁAG\ai-web-factory
       cd C:\GUŁAG\ai-web-factory
       ```
    3. Zainicjuj repozytorium Git:
       ```powershell
       git init
       ```
    4. Utwórz strukturę folderów:
       ```powershell
       mkdir agents config projects tests outputs .github
       ```
-->

<!-- **Krok 2: Automatyczna instalacja systemu**
* Cel: Skonfigurowanie środowiska i instalacja zależności systemu (Python, Node.js, Docker, biblioteki).
* Nowość: Skrypt setup.ps1 automatycznie instaluje wszystkie narzędzia i konfiguruje środowisko.
* Artefakty:
    * setup.ps1
    * .env.example
    * requirements.txt
* Instrukcje:
    1. Zapisz pliki setup.ps1, .env.example, requirements.txt w C:\GUŁAG\ai-web-factory.
    2. Utwórz .env:
       ```powershell
       notepad .env
       ```
       Wklej klucze z .env.example, uzupełniając wartości (np. SUPABASE_SERVICE_KEY).
    3. Uruchom skrypt instalacyjny:
       ```powershell
       cd C:\GUŁAG\ai-web-factory
       .\setup.ps1
       ```
* Weryfikacja:
    ```powershell
    python --version
    node --version
    npm --version
    docker --version
    ```
-->

<!-- **Krok 3: Wdrożenie agentów i CLI**
* Cel: Utworzenie i konfiguracja agentów AI oraz skryptu sterującego.
* Nowość: Zaktualizowano generate_project.py o automatyczne przygotowanie stanowiska developerskiego (instalacja zależności, konfiguracja projektu).
* Artefakty:
    * generate_project.py
    * core_agents.py
    * project_editor_agent.py
    * db_fallback.py
* Instrukcje:
    1. Zapisz pliki generate_project.py, core_agents.py, project_editor_agent.py, db_fallback.py w odpowiednich folderach (C:\GUŁAG\ai-web-factory, C:\GUŁAG\ai-web-factory\agents).
* Weryfikacja agentów:
    ```powershell
    python -c "from agents.core_agents import ProjectPlannerAgent; print(ProjectPlannerAgent().role)"
    ```
-->

<!-- **Krok 4: Konfiguracja Supabase i n8n**
* Cel: Integracja z Supabase i automatyzacja przepływów.
* Artefakt:
    * n8n_project_edit_workflow.json
* Instrukcje:
    1. Skonfiguruj tabele Supabase:
       ```sql
       CREATE TABLE project_generations (
         id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
         project_name TEXT NOT NULL,
         framework TEXT,
         features TEXT,
         start_time TIMESTAMP WITH TIME ZONE,
         end_time TIMESTAMP WITH TIME ZONE,
         status TEXT,
         generated_code_quality REAL,
         error_count INTEGER,
         deployment_url TEXT,
         notes TEXT,
         created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
       );

       CREATE TABLE self_improvements (
         id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
         component_affected TEXT,
         change_description TEXT,
         reasoning TEXT,
         quality_metric_before REAL,
         quality_metric_after REAL,
         implemented_at TIMESTAMP WITH TIME ZONE,
         status TEXT,
         created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
       );

       CREATE TABLE task_queue (
         id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
         command TEXT NOT NULL,
         status TEXT DEFAULT 'pending',
         created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
         completed_at TIMESTAMP WITH TIME ZONE
       );

       CREATE TABLE system_issues (
         id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
         log_source TEXT,
         issue TEXT,
         suggested_fix TEXT,
         timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
       );

       CREATE TABLE feedback (
         id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
         message TEXT NOT NULL,
         project_name TEXT,
         suggestions TEXT,
         status TEXT DEFAULT 'pending',
         created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
       );
       ```
    2. Importuj przepływ n8n:
       * Otwórz: http://localhost:5678
       * Importuj n8n_project_edit_workflow.json.
* Weryfikacja Supabase:
    ```powershell
    python -c "from supabase import create_client; from dotenv import load_dotenv; import os; load_dotenv(); client = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_KEY')); print(client.table('project_generations').select('*').limit(1).execute().data)"
    ```
-->

<!-- **Krok 5: Dokumentacja i instrukcje**
* Cel: Utworzenie dokumentacji dla systemu i projektów.
* Artefakty:
    * README.md
    * SupabaseToDo.json
-->

<!-- **Krok 6: Automatyczne przygotowanie stanowiska developerskiego**
* Cel: System automatycznie konfiguruje środowisko dla każdego projektu (np. Next.js, Flask).
* Implementacja:
    * Funkcja setup_development_environment w generate_project.py instaluje zależności (np. npm install, tailwindcss, flask) i konfiguruje projekt (np. tailwind.config.js).
* Przykłady:
    * Next.js: Instaluje tailwindcss, @playwright/test, generuje tailwind.config.js.
    * Flask: Instaluje flask, python-dotenv.
* Instrukcje:
    * Po wygenerowaniu projektu środowisko jest gotowe do użycia:
      ```powershell
      cd C:\GUŁAG\ai-web-factory\projects\SupabaseToDo
      npm run dev
      ```
-->
-->

**Krok 7: Testowanie systemu**
* Cel: Weryfikacja poprawności konfiguracji i generowania projektów.
* Instrukcje:
    1. Generuj projekt:
       ```powershell
       cd C:\GUŁAG\ai-web-factory
       .\venv\Scripts\Activate.ps1
       python generate_project.py --project SupabaseToDo --framework Next.js --features "Uwierzytelnianie Supabase, tabela todos, TailwindCSS"
       ```
    2. Sprawdź folder projektu:
       ```powershell
       dir C:\GUŁAG\ai-web-factory\projects\SupabaseToDo
       ```
    3. Uruchom lokalnie:
       ```powershell
       cd projects\SupabaseToDo
       npm run dev
       ```
       * Otwórz: http://localhost:3000
    4. Wdróż na Vercel:
       ```powershell
       vercel --prod
       ```

**Krok 8: Integracja z SonarQube i dopracowanie agentów**
* Cel: Pełna integracja z SonarQube (analiza wyników, pętla naprawcza) oraz dopracowanie ról i zadań wszystkich 9 agentów.
* Status: Do implementacji

**Instrukcje obsługi systemu**

**Uruchamianie**
* Aktywacja środowiska:
  ```powershell
  cd C:\GUŁAG\ai-web-factory
  .\venv\Scripts\Activate.ps1
  ```
* Generowanie projektu:
    * Z --features:
      ```powershell
      python generate_project.py --project SupabaseToDo --framework Next.js --features "Uwierzytelnianie Supabase, tabela todos, TailwindCSS"
      ```
    * Z JSON:
      ```powershell
      python generate_project.py --config config\SupabaseToDo.json
      ```
    * Z --functionality i --design:
      ```powershell
      python generate_project.py --project SupabaseToDo --framework Next.js --functionality "Uwierzytelnianie Supabase, tabela todos" --design "TailwindCSS, tryb ciemny"
      ```
    * Edycja projektu:
      ```powershell
      python generate_project.py --project SupabaseToDo --edit --changes "Add dark mode toggle"
      ```
    * Uruchomienie lokalne:
      ```powershell
      cd projects\SupabaseToDo
      npm run dev
      ```
    * Wdrożenie:
      ```powershell
      cd projects\SupabaseToDo
      vercel --prod
      ```

**Monitorowanie**
* Discord: Sprawdź #ai-factory-notifications.
* n8n: http://localhost:5678
* SonarQube: http://localhost:9000
* Supabase: Dashboard (https://jvstwenbkeyewfawsvtc.supabase.co)

**Przekazywanie projektów klientom**
* Instrukcje:
    1. Skompresuj projekt:
       ```powershell
       cd C:\GUŁAG\ai-web-factory\projects\SupabaseToDo
       Compress-Archive -Path . -DestinationPath SupabaseToDo.zip
       ```
    2. Udostępnij:
       * ZIP: Prześlij SupabaseToDo.zip.
       * GitHub: https://github.com/twoj-username/supabase-todo-aifactory
       * Vercel: Podaj URL wdrożenia (np. https://supabase-todo-aifactory.vercel.app).
    3. Dołącz dokumentację:
       * Plik INSTRUCTIONS.md (generowany automatycznie w projekcie).
       * Zmienne środowiskowe (.env.local).
* Artefakt:
    * INSTRUCTIONS.md

**Podsumowanie funkcjonalności**
* Automatyczna instalacja:
    * setup.ps1 instaluje Git, Node.js, Python, Docker, VS Code, biblioteki Pythona (requirements.txt), globalne narzędzia Node.js (create-next-app, vercel), oraz kontenery Docker (n8n, SonarQube).
* Przygotowanie stanowiska developerskiego:
    * Funkcja setup_development_environment w generate_project.py automatycznie konfiguruje środowisko dla projektu (np. npm install, tailwindcss dla Next.js; pip install flask dla Flask).
* Generowanie i edycja projektów:
    * Obsługa --features, --config, --functionality, --design, --edit.
    * Automatyczne tworzenie tabel w Supabase i kodu (Next.js, Flask).
* Wdrożenie:
    * Vercel dla automatycznych wdrożeń.
    * GitHub dla wersjonowania.
* Przekazywanie projektów:
    * ZIP, GitHub, Vercel URL.
    * Dokumentacja (INSTRUCTIONS.md, .env.local).

---

**Twoja perspektywa: System AI Web Factory jako wirtualny zespół**

System AI Web Factory działa jak wirtualny zespół, który tworzy strony i aplikacje webowe zintegrowane z Supabase (np. aplikacja To-Do z uwierzytelnianiem i real-time aktualizacjami). Twoja rola to:

* **Wpisanie polecenia:** W PowerShell lub n8n podajesz projekt, framework i funkcje, w tym Supabase (np. `python generate_project.py --project TodoApp --framework Next.js --features "lista zadań, Supabase, uwierzytelnianie, real-time"`).
* **Skonfigurowanie Supabase:** Raz, tworzysz projekt w Supabase, kopiujesz klucze (URL, anon key) i dodajesz je do .env.
* **Monitorowanie:** Sprawdzasz powiadomienia na Discordzie (np. „Zadanie 1: Next.js z Supabase zainicjowany”, „TodoApp wdrożony: https://todoapp.vercel.app”).
* **Weryfikacja:** Otwierasz aplikację online (https://todoapp.vercel.app) lub lokalnie (http://localhost:3000), sprawdzasz zrzut ekranu (outputs\screenshot.png), raport SonarQube (http://localhost:9000), i testujesz funkcje (np. logowanie, dodawanie zadań).
* **Poprawki:** W ~2–5% przypadków edytujesz kod (np. zmieniasz UI w VS Code) i przesyłasz zmiany (git push).

System autonomicznie (~98%) generuje kod z Supabase:

<!--
```text
[START: Twoje polecenie]
  |
  | (1) Wpisujesz polecenie w PowerShell lub n8n
  |    Przykład: `python generate_project.py --project TodoApp --framework Next.js --features "lista zadań, Supabase, uwierzytelnianie, real-time"`
  |    Czas: ~1 minuta
  v
[ETAP 1: Inicjalizacja projektu]
  | - CrewAI parsuje polecenie (project, framework, features)
  | - n8n uruchamia przepływ `codegen_n8n.json`
  | - Tworzy strukturę: `projects/TodoApp`
  | - Ładuje klucze Supabase z `.env`
  | - Discord: Powiadomienie (np. „Inicjalizacja TodoApp”)
  | - Czas: ~1 minuta
  v
[ETAP 2: Generowanie kodu z Supabase]
  | - CrewAI (agent CodeGenAgent):
  |   - Wysyła zapytania do Gemini (limit 10/minutę, ~6 sekund/zapytanie)
  |   - Generuje kod w etapach:
  |     a) Inicjalizacja (np. Next.js z `@supabase/supabase-js`)
  |     b) Frontend (np. komponenty React z Tailwind CSS, logowanie)
  |     c) Backend (np. API Supabase dla CRUD, real-time WebSocket)
  |     d) Baza (np. tabela `tasks` w Supabase)
   |     e) Testy (np. Playwright dla UI, pytest dla API)
   | - Gemini:
   |   - Temperatura 0.3, max tokens 4096
   |   - Używa SDK Supabase, najlepszych praktyk (ESLint, dokumentacja)
   | - Supabase:
   |   - Tworzy tabelę `tasks` (np. `id`, `title`, `user_id`)
   |   - Konfiguruje uwierzytelnianie (email lub OAuth)
   |   - Ustawia subskrypcje real-time (np. `tasks` changes)
   | - Zapisywanie: Kod w `projects/TodoApp` (np. `pages/index.js`, `lib/supabase.js`)
   | - Discord: Powiadomienia (np. „Frontend z Supabase wygenerowany”)
   | - Czas: ~5–10 minut
   v
[ETAP 3: Weryfikacja kodu (A2A)]
   | - CrewAI:
   |   - Pierwsza weryfikacja (Gemini sprawdza błędy, np. błędne zapytania Supabase)
   |   - Druga weryfikacja (dodaje komentarze, dokumentację, optymalizuje)
   | - n8n:
   |   - Węzeł „VerifyCode”: Sprawdza kod
   |   - Węzeł „SecondVerifyCode”: Optymalizuje, dokumentuje
   | - Wynik: Kod poprawiony (~9.2/10, błędy ~1–3%)
   | - Zapisywanie: Poprawiony kod w `projects/TodoApp`
   | - Discord: Powiadomienia (np. „Kod zweryfikowany”)
   | - Czas: ~3–5 minut
   v
[ETAP 4: Analiza jakości]
   | - n8n wysyła kod do SonarQube (`http://localhost:9000`)
   | - SonarQube:
   |   - Analizuje: Code Smells, Coverage (~85–90%), zgodność z ESLint
   |   - Sprawdza Supabase (np. poprawność zapytań REST)
   |   - Generuje raport (np. „Code Smells: 0, Coverage: 88%”)
   | - Jeśli błędy:
   |   - n8n uruchamia A2A (Gemini poprawia, np. dodaje indeksy w Supabase)
   |   - Powiadomienie Discord: „Błąd naprawiony, sprawdź task_x.txt”
   | - Czas: ~2–3 minuty
   v
[ETAP 5: Testy automatyczne]
   | - CrewAI uruchamia testy:
   |   - Web: Playwright (np. `tests/e2e.js` dla logowania, real-time)
   |   - API: Jest (np. `tests/api.test.js` dla CRUD)
   | - Supabase:
   |   - Testy sprawdzają: CRUD, uwierzytelnianie, subskrypcje WebSocket
   | - Wynik: Raport (np. „Tests: 12 passed, 0 failed”)
   | - Jeśli błędy:
   |   - A2A w n8n poprawia kod
   |   - Powiadomienie Discord: „Testy poprawione”
   | - Zapisywanie: Wyniki w `projects/TodoApp/tests`
   | - Czas: ~2–3 minuty
   v
[ETAP 6: Wdrożenie]
   | - n8n:
   |   - Pushuje kod do GitHub (`git push`)
   |   - Wdraża na Vercel (Next.js) lub Render (Flask/Django)
   | - Vercel/Render:
   |   - Buduje aplikację z Supabase (klucze z `.env`)
   |   - Udostępnia URL (np. `https://todoapp.vercel.app`)
   | - Supabase:
   |   - Aplikacja łączy się z bazą (URL, anon key)
   |   - Uwierzytelnianie i real-time działają
   | - Zrzut ekranu: UI w `outputs\screenshot.png` (np. lista zadań z logowaniem)
   | - Discord: Powiadomienie (np. „Wdrożono: https://todoapp.vercel.app”)
   | - Czas: ~2–3 minuty
   v
[ETAP 7: Twoja weryfikacja]
   | - Otwierasz:
   |   - URL (np. `https://todoapp.vercel.app`)
   |   - Lokalnie:
   |     ```powershell
   |     cd projects\TodoApp
   |     npm install
   |     npm run dev
   |     ```
   |     Otwórz `http://localhost:3000`
   |   - Zrzut ekranu: `start outputs\screenshot.png`
   |   - SonarQube: `http://localhost:9000`
   | - Testujesz:
   |   - Logowanie (email/Google)
   |   - Dodawanie/usuwanie zadań (CRUD)
   |   - Real-time (np. zadania aktualizują się po dodaniu przez innego użytkownika)
   | - Jeśli poprawki (~2–5% przypadków):
   |   - Edytujesz w VS Code (np. zmieniasz Tailwind CSS w `styles.css`)
   |   - Pushujesz:
   |     ```powershell
   |     git add .
   |     git commit -m "Poprawki UI"
   |     git push
   |     ```
   |   - Vercel aktualizuje aplikację.
   | - Czas: ~1–15 minut (weryfikacja ~1–2 minuty, poprawki ~10–15 minut)
   v
[KONIEC: Gotowy projekt]
 * Projekt w `projects/TodoApp`
 * Działa lokalnie i online z Supabase
 * Jakość: ~9.2/10, błędy: ~1–3%
 * Całkowity czas: ~10–20 minut
```
-->

**Specyfika Supabase**

**Zalety:**
* Łatwa integracja: SDK dla JavaScript/Python, automatyczne API REST.
* Uwierzytelnianie: Wbudowane (email, OAuth), gotowe komponenty.
* Real-time: WebSocket dla aktualizacji w czasie rzeczywistym.
* PostgreSQL: Potężna baza z indeksami, trigrami, JSONB.
* Chmura: Nie obciąża laptopa (RTX 4060 Ti używany tylko do lokalnych testów).

**Wyzwania:**
* Konfiguracja: Musisz ręcznie stworzyć projekt Supabase i dodać klucze do .env.
* Limity darmowego planu: Supabase ma limity (np. 500 MB storage, 2 GB transferu/miesiąc), ale wystarczają dla prototypów.
* Złożone zapytania: Bardzo zaawansowane zapytania (np. złożone JOINy) mogą wymagać ręcznej optymalizacji (~2–5% przypadków).
* Rozwiązanie: System A2A i SonarQube minimalizują błędy, a Gemini generuje zoptymalizowane zapytania.

**Windows 11:**
* Docker Desktop: Obsługuje n8n i SonarQube (WSL 2).
* PowerShell/VS Code: Intuicyjne dla poleceń i edycji kodu.
* RTX 4060 Ti: Przydatny do lokalnych testów (np. rendering Next.js).

**Podsumowanie**

**Jak działa z Supabase:**
* System generuje strony/aplikacje z Supabase (tabele, API REST, uwierzytelnianie, real-time), integrując SDK (@supabase/supabase-js, supabase-py).
* Proces: Polecenie → generowanie kodu → weryfikacja A2A → analiza SonarQube → testy → wdrożenie → weryfikacja.
* Limit 10 zapytań/minutę wydłuża czas (~10–20 minut), ale zapewnia jakość ~9.2/10, błędy ~1–3%.

**Twoja rola:**
* Konfigurujesz Supabase raz (~10 minut): tworzysz projekt, dodajesz klucze do .env.
* Wpisujesz polecenie (~1 minuta).
* Monitorujesz Discord (~10–20 minut, w tle).
* Weryfikujesz wyniki (~1–2 minuty).
* Poprawiasz (~10–15 minut w ~2–5% przypadków).

**Projekty z Supabase:**
* Strony: Next.js z listą zadań, logowaniem, real-time.
* Aplikacje: Flask/Django z API, uwierzytwi