@echo off
rem THE SILK ROAD - 3D maps launcher (Fadak 8/16).
rem Opens the game in a browser session that allows local map images into WebGL
rem (its own separate profile - your normal browsing profile is untouched).
set GAME=%~dp0index.html
set FLAGS=--allow-file-access-from-files --user-data-dir="%TEMP%\silkroad3d"
where chrome >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" chrome %FLAGS% "file:///%GAME:\=/%"
) else (
  start "" msedge %FLAGS% "file:///%GAME:\=/%"
)
