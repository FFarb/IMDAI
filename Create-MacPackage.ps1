# PowerShell Script to Create IMDAI Mac Installer Package
# Run this on Windows to create a package for Mac users

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  IMDAI Mac Package Creator" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Get current directory
$projectPath = Get-Location

Write-Host "Creating Mac installer package..." -ForegroundColor Yellow
Write-Host ""

# Define what to include
$itemsToInclude = @(
    "backend",
    "frontend",
    "data",
    "Setup IMDAI.command",
    "INSTALLATION_INSTRUCTIONS.txt",
    "README.md"
)

Write-Host "Checking required files..." -ForegroundColor Yellow

# Check if required files exist
$missingFiles = @()
foreach ($item in $itemsToInclude) {
    if (-not (Test-Path $item)) {
        $missingFiles += $item
        Write-Host "  Missing: $item" -ForegroundColor Red
    } else {
        Write-Host "  Found: $item" -ForegroundColor Green
    }
}

if ($missingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "ERROR: Some required files are missing!" -ForegroundColor Red
    Write-Host "Please make sure all files exist before running this script." -ForegroundColor Red
    pause
    exit 1
}

Write-Host ""
Write-Host "All required files found!" -ForegroundColor Green
Write-Host ""

# Create the ZIP file
$zipName = "IMDAI-Mac-Installer.zip"
$zipPath = Join-Path $projectPath $zipName

if (Test-Path $zipPath) {
    Write-Host "Removing old ZIP file..." -ForegroundColor Yellow
    Remove-Item $zipPath -Force
}

Write-Host "Creating ZIP file..." -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Gray
Write-Host ""

# Create ZIP with only the necessary files
try {
    Compress-Archive -Path $itemsToInclude -DestinationPath $zipPath -CompressionLevel Optimal -Force
    
    # Get file size
    $zipSize = (Get-Item $zipPath).Length / 1MB
    
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host "  Package Created Successfully!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "File: $zipName" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "Location: $zipPath" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "What to do next:" -ForegroundColor Yellow
    Write-Host "1. Send $zipName to your Mac user" -ForegroundColor White
    Write-Host "2. Tell them to extract it" -ForegroundColor White
    Write-Host "3. Tell them to double-click Setup IMDAI.command" -ForegroundColor White
    Write-Host ""
    Write-Host "Done!" -ForegroundColor Green
    Write-Host ""
    
    # Open folder
    explorer.exe /select,$zipPath
    
} catch {
    Write-Host ""
    Write-Host "ERROR creating ZIP file:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    pause
    exit 1
}
