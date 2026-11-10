@echo off
rem Live incident demo on port 8502 (the full prototype stays on 8501).
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python -m streamlit run dashboard\live_app.py --server.port 8502
