@echo off
echo ============================================
echo  pgvector v0.8.2 installer for PostgreSQL 17
echo ============================================
echo.

set SRC=%TEMP%\pgvector_pg17
set PGLIB=C:\Program Files\PostgreSQL\17\lib
set PGEXT=C:\Program Files\PostgreSQL\17\share\extension

echo Copying vector.dll ...
copy /Y "%SRC%\lib\vector.dll" "%PGLIB%\vector.dll"
if errorlevel 1 (
    echo ERROR: Could not copy vector.dll. Make sure you are running as Administrator.
    pause
    exit /b 1
)

echo Copying extension SQL and control files ...
xcopy /Y /Q "%SRC%\share\extension\*" "%PGEXT%\"
if errorlevel 1 (
    echo ERROR: Could not copy extension files.
    pause
    exit /b 1
)

echo Restarting PostgreSQL 17 service ...
net stop postgresql-x64-17
net start postgresql-x64-17

echo.
echo ============================================
echo  Done! pgvector installed successfully.
echo  Now run: python src/seed_db.py --reset
echo ============================================
pause
