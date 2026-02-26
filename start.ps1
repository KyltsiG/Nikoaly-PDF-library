# PDF Library - Start Script

# Activate virtual environment
.\venv\Scripts\Activate.ps1


# Open the API documentation in the default web browser



# Start the server
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000


