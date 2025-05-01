#!/bin/bash

echo "Script execution started."

# AI Web Factory Start Script for Linux/macOS
# Uruchamia system jednym kliknięciem, konfigurując środowisko i zależności

# Kolory dla komunikatów
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Katalog projektu
PROJECT_DIR="$HOME/ai-web-factory"
REPO_URL="https://github.com/Barczakson/ai-web-factory.git"
BRANCH="natural-language-parser"

# Domyślny prompt (można zmienić interaktywnie)
DEFAULT_PROMPT="Stwórz aplikację TodoApp z Next.js i Supabase oraz uwierzytelnianiem"

echo -e "${GREEN}=== Uruchamianie AI Web Factory ===${NC}"

# Sprawdzenie wymagań systemowych
echo -e "${YELLOW}Sprawdzanie wymagań systemowych...${NC}"
command -v python3 >/dev/null 2>&1 || { echo -e "${RED}Błąd: Python3 nie jest zainstalowany. Zainstaluj: sudo apt install python3${NC}"; exit 1; }
command -v git >/dev/null 2>&1 || { echo -e "${RED}Błąd: Git nie jest zainstalowany. Zainstaluj: sudo apt install git${NC}"; exit 1; }
command -v redis-server >/dev/null 2>&1 || { echo -e "${RED}Błąd: Redis nie jest zainstalowany. Zainstaluj: sudo apt install redis-server${NC}"; exit 1; }

# Sprawdzenie wersji Pythona
PYTHON_VERSION=$(python3 --version | grep -oP '\d+\.\d+')
if [[ "$PYTHON_VERSION" < "3.10" ]]; then
    echo -e "${RED}Błąd: Wymagany Python 3.10 lub nowszy. Aktualna wersja: $PYTHON_VERSION${NC}"
    exit 1
fi

# Klonowanie lub aktualizacja repozytorium
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Klonowanie repozytorium...${NC}"
    git clone --branch "$BRANCH" "$REPO_URL" "$PROJECT_DIR" || { echo -e "${RED}Błąd: Nie udało się sklonować repozytorium${NC}"; exit 1; }
else
    echo -e "${YELLOW}Aktualizacja repozytorium...${NC}"
    cd "$PROJECT_DIR" || exit
    git pull origin "$BRANCH" || { echo -e "${RED}Błąd: Nie udało się zaktualizować repozytorium${NC}"; exit 1; }
fi

cd "$PROJECT_DIR" || { echo -e "${RED}Błąd: Nie udało się przejść do katalogu $PROJECT_DIR${NC}"; exit 1; }

# Utworzenie i aktywacja środowiska wirtualnego
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Tworzenie środowiska wirtualnego...${NC}"
    python3 -m venv venv || { echo -e "${RED}Błąd: Nie udało się utworzyć środowiska wirtualnego${NC}"; exit 1; }
fi
source venv/bin/activate || { echo -e "${RED}Błąd: Nie udało się aktywować środowiska wirtualnego${NC}"; exit 1; }

# Instalacja zależności
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Instalacja zależności...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt || { echo -e "${RED}Błąd: Nie udało się zainstalować zależności${NC}"; exit 1; }
else
    echo -e "${RED}Błąd: Brak pliku requirements.txt${NC}"
    exit 1
fi

# Uruchomienie Redis
echo -e "${YELLOW}Sprawdzanie Redis...${NC}"
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}Uruchamianie serwera Redis...${NC}"
    sudo systemctl start redis || { echo -e "${RED}Błąd: Nie udało się uruchomić Redis. Sprawdź instalację: sudo apt install redis-server${NC}"; exit 1; }
    redis-cli ping >/dev/null 2>&1 || { echo -e "${RED}Błąd: Redis nadal nie działa${NC}"; exit 1; }
fi
echo -e "${GREEN}Redis działa${NC}"

# Konfiguracja .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Konfiguracja pliku .env...${NC}"
    cp .env.example .env || { echo -e "${RED}Błąd: Brak pliku .env.example${NC}"; exit 1; }
    echo -e "${YELLOW}Podaj klucz GEMINI_API_KEY (uzyskaj z https://ai.google.dev/):${NC}"
    read -r GEMINI_API_KEY
    if [ -z "$GEMINI_API_KEY" ]; then
        echo -e "${RED}Błąd: Klucz GEMINI_API_KEY nie może być pusty${NC}"
        exit 1
    fi
    echo "GEMINI_API_KEY=$GEMINI_API_KEY" >> .env
    echo -e "${YELLOW}Podaj SUPABASE_URL (opcjonalne, naciśnij Enter, aby pominąć):${NC}"
    read -r SUPABASE_URL
    [ -n "$SUPABASE_URL" ] && echo "SUPABASE_URL=$SUPABASE_URL" >> .env
    echo -e "${YELLOW}Podaj SUPABASE_SERVICE_KEY (opcjonalne, naciśnij Enter, aby pominąć):${NC}"
    read -r SUPABASE_SERVICE_KEY
    [ -n "$SUPABASE_SERVICE_KEY" ] && echo "SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY" >> .env
    echo "LITELLM_LOG=DEBUG" >> .env
fi

# Wybór promptu
echo -e "${YELLOW}Wpisz polecenie (np. 'Stwórz aplikację TodoApp z Next.js i Supabase') lub naciśnij Enter dla domyślnego: '$DEFAULT_PROMPT'${NC}"
read -r USER_PROMPT
PROMPT="${USER_PROMPT:-$DEFAULT_PROMPT}"

# Uruchomienie systemu
echo -e "${YELLOW}Uruchamianie AI Web Factory z poleceniem: '$PROMPT'...${NC}"
python generate_project.py --prompt "$PROMPT" > logs.txt 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Sukces: System uruchomiony. Wyniki w katalogu projects/. Logi w logs.txt${NC}"
else
    echo -e "${RED}Błąd: Nie udało się uruchomić systemu. Sprawdź logs.txt${NC}"
    cat logs.txt
    exit 1
fi

echo -e "${GREEN}=== Zakończono ===${NC}"