@echo off
cd /d %~dp0

REM 仮想環境ON
call .venv\Scripts\activate.bat

REM データ更新（取得→集計→書き出し）
python -m scripts.fetch_xpt001
if errorlevel 1 goto :error

python -m scripts.aggregate_h3
if errorlevel 1 goto :error

python -m scripts.build
if errorlevel 1 goto :error

REM 変更があるときだけcommit/pushする
git add docs\data\latest.geojson docs\data\meta.json

git diff --cached --quiet
if %errorlevel%==0 (
  echo No data changes. Done.
  goto :end
)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM"') do set YM=%%i
git commit -m "data: update %YM%"
git push
goto :end

:error
echo.
echo ERROR: Update failed.
echo Please scroll up and read the red error message.
pause
exit /b 1

:end
echo.
echo Done.
