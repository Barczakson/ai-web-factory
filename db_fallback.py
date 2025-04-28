import sqlite3
import os

def load_project_metadata(project_name):
    """
    Ładuje metadane projektu z lokalnej bazy SQLite.
    Args:
        project_name (str): Nazwa projektu.
    Returns:
        dict: Metadane projektu (framework, features) lub None, jeśli nie znaleziono.
    """
    db_path = os.path.join("/app", "projects.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT framework, features FROM projects WHERE project_name = ?",
            (project_name,)
        )
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "framework": result[0],
                "features": result[1]
            }
        else:
            return None
    except sqlite3.Error as e:
        print(f"BŁĄD: Nie można załadować metadanych z SQLite: {e}")
        return None