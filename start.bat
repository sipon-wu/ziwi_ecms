@echo off
echo Starting ZiWi Energy Carbon System...
cd /d "D:/工业元/数云_新质力/ziwi_project_dna/backend"
start /b "" C:/Python314/python.exe -m uvicorn main:app --host 0.0.0.0 --port 8088
cd /d "D:/工业元/数云_新质力/ziwi_project_dna/frontend"
start /b "" npx vite --host 0.0.0.0 --port 5173
echo.
echo Backend : http://localhost:8088
echo Frontend: http://localhost:5173
echo Run stop.bat to shutdown.
pause
