# .claude/hooks/run-tests-if-py.ps1
# PostToolUse hook: runs full pytest suite after any Edit|Write on a .py file.
# Fase 2 enforcement layer (ROADMAP.md v2.0).
# Uses the project venv's pytest directly (by path), so it does not depend
# on the venv being activated in the PowerShell session that launched Claude Code.

$callInput = [Console]::In.ReadToEnd() | ConvertFrom-Json
$filePath = $callInput.tool_input.file_path

if ($filePath -notmatch '\.py$') {
    exit 0
}

Set-Location $env:CLAUDE_PROJECT_DIR

$venvPytest = Join-Path $env:CLAUDE_PROJECT_DIR "venv\Scripts\pytest.exe"

if (Test-Path $venvPytest) {
    & $venvPytest --tb=short -q
} else {
    Write-Warning "venv pytest not found at $venvPytest, falling back to PATH pytest"
    pytest --tb=short -q
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "PostToolUse gate: pytest FAILED after editing $filePath"
    exit 2
}

exit 0