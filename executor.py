import os
import tempfile
import json
import subprocess
import uuid
import platform

def execute_script(script):
    # Create a temporary file with a unique name to store the script
    temp_dir = tempfile.gettempdir()
    script_id = str(uuid.uuid4())
    temp_path = os.path.join(temp_dir, f"script_{script_id}.py")
    
    try:
        # Add wrapper to capture the return value and ensure it's JSON
        wrapped_script = '''
import json
import sys
import traceback

# Original script
{}

# Validation and execution
if __name__ == "__main__":
    try:
        # Check if main is defined
        if 'main' not in globals():
            print("__ERROR__")
            print("Error: Script must define a main() function")
            sys.exit(1)
            
        # Execute main
        result = main()
        
        # Validate that the result is JSON serializable
        try:
            json_result = json.dumps(result)
            print("__RESULT__")
            print(json_result)
        except Exception as e:
            print("__ERROR__")
            print(f"Error: main() function must return JSON serializable data: {{str(e)}}")
            sys.exit(1)
    except Exception as e:
        print("__ERROR__")
        print(f"Error during execution: {{traceback.format_exc()}}")
        sys.exit(1)
'''.format(script)
        
        # Write the wrapped script to the temporary file
        with open(temp_path, 'w') as f:
            f.write(wrapped_script)
        
        # Try using nsjail first
        if platform.system() == "Linux":
            try:
                # Execute the script using nsjail for security on Linux
                cmd = [
                    "/usr/local/bin/nsjail",
                    "--config", "/app/nsjail.config",
                    "--", "python3", temp_path
                ]
                
                # Run the process and capture output
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                stdout, stderr = process.communicate(timeout=30)  # Add timeout
                
                # Check if nsjail worked
                if process.returncode == 0 or not "Couldn't launch the child process" in stderr:
                    # Process nsjail output normally
                    pass
                else:
                    # If nsjail failed, fall back to direct execution
                    raise Exception("nsjail execution failed, falling back to direct execution")
                
            except Exception as e:
                # Fall back to subprocess if nsjail fails (for non-Linux systems or if nsjail has issues)
                cmd = ["python3", temp_path]
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                stdout, stderr = process.communicate(timeout=30)
        else:
            # For non-Linux systems (macOS, Windows), use subprocess directly
            cmd = ["python3", temp_path]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            stdout, stderr = process.communicate(timeout=30)
        
        # Check for errors in stderr
        if stderr and not "__ERROR__" in stdout:
            return None, "", f"Execution error: {stderr}"
        
        # Extract the result and stdout
        result = None
        stdout_lines = stdout.splitlines()
        real_stdout = []
        in_result = False
        error_message = None
        
        for i, line in enumerate(stdout_lines):
            if line == "__RESULT__":
                in_result = True
                # The next line should contain the JSON result
                if i + 1 < len(stdout_lines):
                    try:
                        result = json.loads(stdout_lines[i + 1])
                    except json.JSONDecodeError:
                        error_message = "Failed to parse JSON result"
                break
            elif line == "__ERROR__":
                # Collect error message from the next lines
                error_parts = stdout_lines[i+1:]
                error_message = "\n".join(error_parts)
                break
            else:
                real_stdout.append(line)
        
        # If we found an error but no error_message, check stderr
        if error_message is None and process.returncode != 0:
            error_message = stderr
        
        if error_message:
            return None, "\n".join(real_stdout), error_message
        
        return result, "\n".join(real_stdout), None
    
    except subprocess.TimeoutExpired:
        return None, "", "Execution timed out after 30 seconds"
    except Exception as e:
        return None, "", f"Internal error: {str(e)}"
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
