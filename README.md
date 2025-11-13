
LegacyOnboard AI — Prototype (Streamlit)
---------------------------------------

Files:
- app.py : the Streamlit prototype application
- requirements.txt : Python dependencies
- README.md : this file

How to run (local machine):
1. Create and activate a Python 3.10+ virtual environment.
2. Install dependencies:
   pip install -r requirements.txt
3. Run the app:
   streamlit run app.py
4. By default the app runs in MOCK mode (no API keys needed). To enable real OpenAI calls, set your OPENAI_API_KEY in the environment and choose OPENAI mode in the sidebar:

   export OPENAI_API_KEY='sk-...'
   streamlit run app.py

Notes:
- The OPENAI mode will attempt to call the ChatCompletion endpoint. Replace the model name in app.py to a model available on your account if necessary.
- This prototype intentionally avoids storing uploaded files and keeps processing local to the running app. For production you should:
  - Add secure transport (HTTPS)
  - Use encrypted storage and strict access controls
  - Add audit logging and consent screens for PII
  - Implement robust document parsing and validation (OCR for images/PDFs)
- This package is for demonstration / course submission purposes only.
