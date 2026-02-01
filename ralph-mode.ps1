# Copilot Ralph Mode - PowerShell Wrapper
# Usage: .\ralph-mode.ps1 <command> [options]

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
python "$scriptPath\ralph_mode.py" $args
