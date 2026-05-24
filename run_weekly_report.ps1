# FI Community Weekly Report — Windows Task Scheduler Script
# Runs every Monday at 7:00 AM
# Logs output to: C:\Users\Kai\Documents\AI Automation\logs\

$ProjectDir = "c:\Users\Kai\Documents\AI Automation"
$LogDir     = "$ProjectDir\logs"
$Date       = Get-Date -Format "yyyy-MM-dd"
$LogFile    = "$LogDir\$Date-weekly-report.log"

# Ensure log directory exists
if (-not (Test-Path $LogDir)) { New-Item -ItemType Directory -Path $LogDir | Out-Null }

function Log($msg) {
    $ts = Get-Date -Format "HH:mm:ss"
    "$ts  $msg" | Tee-Object -FilePath $LogFile -Append
}

Log "=== FI Community Weekly Report — $Date ==="
Log "Starting report generation..."

Set-Location $ProjectDir

# Run Claude Code non-interactively with the weekly workflow prompt
$prompt = @"
Follow the workflow at workflows/weekly-report-workflow.md exactly.
Today's date is $Date.
Generate the FI Community weekly intelligence report.
Save all outputs to the output/ folder with date prefix $Date.
After generating the PDF, commit and push to GitHub.
"@

try {
    Log "Running Claude Code CLI..."
    # Redirect stdin from null to suppress the "no stdin" warning in non-interactive mode
    $output = cmd /c "echo. | claude -p ""$prompt"" --allowedTools Bash,Read,Write,Edit,Glob,Grep,WebSearch 2>&1"
    Log $output

    # Verify the PDF was created
    $pdf = "$ProjectDir\output\$Date-weekly-report.pdf"
    if (Test-Path $pdf) {
        $size = [math]::Round((Get-Item $pdf).Length / 1KB, 0)
        Log "SUCCESS: PDF created — $pdf ($size KB)"
    } else {
        Log "WARNING: PDF not found at expected path. Check Claude output above."
    }
} catch {
    Log "ERROR: $_"
}

Log "=== Report run complete ==="
