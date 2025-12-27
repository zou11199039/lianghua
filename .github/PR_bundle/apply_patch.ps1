<#
PowerShell script to apply bundled files to the repository.
It will backup existing files (appending .bak) and then copy the new files into place.
#>

$base = Split-Path -Parent $MyInvocation.MyCommand.Definition
$filesDir = Join-Path $base 'files'

$mapping = @{
    'src_data_qmt_client.py' = 'src/data/qmt_client.py'
    'ci_workflow.yml' = '.github/workflows/ci.yml'
    'test_qmt_client.py' = 'tests/test_qmt_client.py'
    'test_receipt_parser_xtquant.py' = 'tests/test_receipt_parser_xtquant.py'
    'ci-qmt-client-draft.md' = '.github/PRs/ci-qmt-client-draft.md'
}

Write-Host "Applying PR bundle files..."

foreach ($key in $mapping.Keys) {
    $src = Join-Path $filesDir $key
    $dest = Join-Path (Get-Location) $mapping[$key]

    if (-not (Test-Path $src)) {
        Write-Host "Missing bundle file: $src" -ForegroundColor Red
        continue
    }

    $destDir = Split-Path -Parent $dest
    if (-not (Test-Path $destDir)) {
        Write-Host "Creating directory $destDir"
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }

    if (Test-Path $dest) {
        $bak = "$dest.bak"
        Write-Host "Backing up $dest -> $bak"
        Copy-Item -Path $dest -Destination $bak -Force
    }

    Write-Host "Copying $src -> $dest"
    Copy-Item -Path $src -Destination $dest -Force
}

Write-Host "Done. Please run tests: .\.venv\Scripts\Activate.ps1; python -m pytest -q"
Write-Host "Then create a branch and commit the changes (see .github/PR_bundle/README.md for instructions)."