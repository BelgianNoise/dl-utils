$bundleName = "./dl-downer-bundle.zip"
$root = Resolve-Path "$PSScriptRoot/.."
Set-Location $root

if (Test-Path $bundleName) {
    $answer = Read-Host "$bundleName already exists. Overwrite? (y/n)"
    if ($answer -ne 'y') {
        Write-Host "Aborted."
        exit 1
    }
    Remove-Item $bundleName
}

# Check if Compress-Archive is available (PowerShell 5+)
if (Get-Command Compress-Archive -ErrorAction SilentlyContinue) {
    # Remove __pycache__ folders temporarily
    $exclude = Get-ChildItem -Path .\src -Recurse -Directory -Filter "__pycache__"
    foreach ($dir in $exclude) { Remove-Item $dir.FullName -Recurse -Force }
    Compress-Archive -Path cli.py,src -DestinationPath $bundleName
    Write-Host "Created $bundleName"
} else {
    Write-Host "Compress-Archive not available. Please use a zip tool manually."
    exit 1
}
