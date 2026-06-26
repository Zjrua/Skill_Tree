@echo off
REM ============================================================
REM  build_profile.cmd - Build one or all resume profiles to PDF
REM  Usage:
REM    build_profile.cmd                    build all profiles
REM    build_profile.cmd recommendation     build one profile
REM  Output: resume\build\<profile>.pdf
REM ============================================================
setlocal enabledelayedexpansion

set "RESUME_DIR=%~dp0.."
set "BILLRYAN=%RESUME_DIR%\templates\billryan"

if not exist "%BILLRYAN%\resume.cls" (
    echo [ERROR] billryan template not found: %BILLRYAN%
    exit /b 1
)

set "TARGET=%~1"
if "%TARGET%"=="" (
    set "PROFILE_LIST=recommendation search ads"
) else (
    set "PROFILE_LIST=%TARGET%"
)

set "SUCCESS=0"
set "FAILED=0"

for %%P in (%PROFILE_LIST%) do (
    if not exist "%RESUME_DIR%\profiles\%%P\build.tex" (
        echo [SKIP] %%P - no build.tex
    ) else (
        echo.
        echo ====== Building profile: %%P ======
        set "TEXINPUTS=%RESUME_DIR%\shared\;%RESUME_DIR%\profiles\%%P\;"
        REM xelatex log goes to <jobname>.log; keep _build.log minimal redirect
        pushd "%BILLRYAN%"
        xelatex -interaction=nonstopmode -halt-on-error -jobname="%%P" -output-directory="%RESUME_DIR%\build" "%RESUME_DIR%\profiles\%%P\build.tex" >nul 2>&1
        popd
        if exist "%RESUME_DIR%\build\%%P.pdf" (
            echo [OK]   %%P.pdf
            set /a SUCCESS+=1
        ) else (
            echo [FAIL] %%P - see %%P.log in build dir
            set /a FAILED+=1
        )
    )
)

REM Clean intermediate files, keep .pdf and xelatex .log (for debugging)
pushd "%RESUME_DIR%\build"
for %%E in (aux out synctex.gz toc fls fdb_latexmk bbl blg) do del /q *.%%E 2>nul
popd

echo.
echo ====== Done: !SUCCESS! ok, !FAILED! failed ======
echo PDFs in: %RESUME_DIR%\build\
endlocal
exit /b 0
