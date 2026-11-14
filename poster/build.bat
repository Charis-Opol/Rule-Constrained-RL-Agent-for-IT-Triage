@echo off
rem Rebuilds the scientific-writing (research status) poster, A0 landscape PowerPoint:
rem   poster\Opol_Charis_Scientific_Writing_Poster.pptx
rem It uses the same template as the pilot poster (documentation\pilot-report\build_poster.py).
cd /d "%~dp0.."
".venv\Scripts\python.exe" poster\build_writing_poster.py || goto :error
goto :eof
:error
echo Build failed.
exit /b 1
