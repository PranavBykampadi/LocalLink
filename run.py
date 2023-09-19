# run.py
import sys
import os

# Add the project root directory to the Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from app import app

if __name__ == '__main__':
    app.run(debug=True)
