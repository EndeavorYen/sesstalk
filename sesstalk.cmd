@echo off
setlocal
set "SCRIPT=%~dp0sesstalk.py"
if defined SESSTALK_PYTHON (
  "%SESSTALK_PYTHON%" -S "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)
if exist "%USERPROFILE%\miniconda3\python.exe" (
  "%USERPROFILE%\miniconda3\python.exe" -S "%SCRIPT%" %*
  exit /b %ERRORLEVEL%
)
python -S "%SCRIPT%" %*
