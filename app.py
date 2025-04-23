from flask import Flask, request, jsonify
import json
import re
from executor import execute_script

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'})

@app.route('/execute', methods=['POST'])
def execute():
    # Extract the script from the request
    try:
        data = request.get_json()
    except Exception:
        return jsonify({'error': 'Invalid JSON in request body'}), 400
    
    if not data or not isinstance(data, dict):
        return jsonify({'error': 'Request body must be a JSON object'}), 400
    
    if 'script' not in data:
        return jsonify({'error': 'Missing "script" field in request body'}), 400
    
    script = data['script']
    
    if not isinstance(script, str):
        return jsonify({'error': '"script" must be a string'}), 400
    
    # Basic validation - check for main() function
    if not re.search(r'def\s+main\s*\(\s*\)\s*:', script):
        return jsonify({'error': 'Script must contain a main() function with no parameters'}), 400
    
    # Execute the script
    result, stdout, error = execute_script(script)
    
    if error:
        return jsonify({'error': error}), 400
    
    # Return the result
    return jsonify({
        'result': result,
        'stdout': stdout
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)
