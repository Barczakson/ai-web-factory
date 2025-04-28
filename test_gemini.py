from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv() # Załaduj zmienne środowiskowe z .env

google_api_key = os.getenv("GOOGLE_API_KEY")
llm_model = os.getenv("LITELLM_MODEL", "gemini-2.0-flash") # Użyj LITELLM_MODEL z .env, domyślnie gemini-2.0-flash

if not google_api_key:
    print("Błąd: Zmienna środowiskowa GOOGLE_API_KEY nie jest ustawiona.")
else:
    try:
        # Użyj nazwy modelu z .env lub domyślnej
        llm = ChatGoogleGenerativeAI(
            model=llm_model,
            google_api_key=google_api_key
        )
        print(f"Próba wywołania modelu: {llm_model}")
        response = llm.invoke("Witaj, świecie!")
        print("Odpowiedź z modelu:")
        print(response.content)
    except Exception as e:
        print(f"Wystąpił błąd podczas wywoływania modelu: {e}")