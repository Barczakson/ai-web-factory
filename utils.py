import os

def get_secret(secret_name):
    """
    Retrieves a secret from Docker secrets or environment variables.
    Prioritizes Docker secrets if available.
    """
    try:
        # Attempt to read from Docker secrets
        with open(f'/run/secrets/{secret_name}', 'r') as secret_file:
            return secret_file.read().strip()
    except IOError:
        # Fallback to environment variables if Docker secret not found
        return os.getenv(secret_name.upper())