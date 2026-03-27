@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
	".venv\Scripts\python.exe" -m webapp.server
) else (
	python -m webapp.server
)
endlocal
