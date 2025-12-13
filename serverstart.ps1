venv/scripts/activate
cd app
waitress-serve --host=0.0.0.0 --port=8000 main:app
pause