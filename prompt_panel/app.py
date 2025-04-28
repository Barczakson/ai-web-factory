from flask import Flask, render_template, request, redirect, url_for
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_script', methods=['POST'])
def run_script():
    project = request.form.get('project', '')
    framework = request.form.get('framework', '')
    features = request.form.get('features', '')
    edit = request.form.get('edit', '')
    changes = request.form.get('changes', '')

    # Construct the command to run generate_project.py
    # Assuming generate_project.py is in the parent directory of prompt_panel
    script_path = os.path.join(os.path.dirname(__file__), '..', 'generate_project.py')
    command = ['python', script_path]

    if project:
        command.extend(['--project', project])
    if framework:
        command.extend(['--framework', framework])
    if features:
        command.extend(['--features', features])
    if edit:
        command.extend(['--edit', edit])
    if changes:
        command.extend(['--changes', changes])

    result = None
    error = None
    try:
        # Run the script as a subprocess
        # Consider activating a virtual environment if necessary
        # For now, assuming python and the script's dependencies are in the PATH
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        result = stdout.decode('utf-8')
        error = stderr.decode('utf-8')
    except Exception as e:
        error = str(e)

    # For now, just redirect back to the index or show a simple status
    # A more robust solution would stream logs or display results properly
    if error:
        return f"Error running script: <pre>{error}</pre>"
    else:
        return f"Script output: <pre>{result}</pre>"

if __name__ == '__main__':
    # Consider running with debug=True for development: app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)