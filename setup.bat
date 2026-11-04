@echo off
rem fullstack-agent setup — find a working Python, then run the setup script.
rem Phase 3 bootstrap (Windows). The python on PATH is often the Microsoft
rem Store stub that exits without running, so prefer the py launcher.
py -3 setup.py %*
if errorlevel 1 (
  echo.
  echo   Could not find a working Python via the py launcher. Install Python 3 first, then re-run setup.
  pause
  exit /b 1
)
