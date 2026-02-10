"""Startup runner for the backend server."""
import sys
import os

# Ensure backend directory is in path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

print(f"Working directory: {os.getcwd()}", flush=True)
print(f"Python: {sys.executable}", flush=True)

try:
    from main import app
    print(f"Application loaded: {app.title}", flush=True)
except Exception as e:
    print(f"ERROR loading app: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

import uvicorn
print("Starting server on http://127.0.0.1:8000", flush=True)
uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
