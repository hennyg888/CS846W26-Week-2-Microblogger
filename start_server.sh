#!/bin/bash

# Start the Gunicorn server with 4 workers and 2 threads per worker
# Binding to localhost on port 5000
python -m waitress --port=5000 server:app