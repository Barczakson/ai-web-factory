from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import subprocess
import os
from dotenv import load_dotenv
import logging

# Konfiguracja logowania
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__, template_folder='prompt_panel/templates')

CORS(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_project():
    data = request.get_json()
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    # Walidacja promptu
    if not prompt.startswith("--") and "dodaj" not in prompt.lower() and "add" not in prompt.lower():
        return jsonify({'error': 'Invalid prompt format'}), 400

    try:
        # Uruchom generate_project.py z podanym promptem
        env = os.environ.copy()
        env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")
        result = subprocess.run(
            ['python', 'generate_project.py'] + prompt.split(),
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            env=env
        )
        if result.returncode == 0:
            return jsonify({'result': result.stdout})
        else:
            return jsonify({'error': result.stderr}), 500
    except Exception as e:
        logger.error(f"Error generating project: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)