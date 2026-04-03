param(
    [ValidateSet("GUI", "CLI", "Both")]
    [string]$Target = "GUI",
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$DistDir = Join-Path $ProjectRoot "dist"
$PrimaryIconPath = Join-Path $ProjectRoot "ico\\app_icon.ico"
$FallbackIconPath = Join-Path $ProjectRoot "app_icon.ico"
$SourceIconPath = if (Test-Path -LiteralPath $PrimaryIconPath) { $PrimaryIconPath } else { $FallbackIconPath }
$TempIconPath = Join-Path $env:TEMP "noir_search_icon.ico"

if (Test-Path -LiteralPath $SourceIconPath) {
    Copy-Item -LiteralPath $SourceIconPath -Destination $TempIconPath -Force
}

function Invoke-PyInstallerBuild {
    param(
        [string]$EntryScript,
        [string]$ExecutableName,
        [bool]$Windowed
    )

    $arguments = @(
        "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name", $ExecutableName,
        "--icon", $TempIconPath,
        "--hidden-import", "selenium.webdriver.edge.webdriver",
        "--add-data", "queries.txt;.",
        "--add-data", "edgedriver_win64;edgedriver_win64"
    )

    if ($Windowed) {
        $arguments += "--windowed"
    }

    $arguments += $EntryScript
    & $PythonExe @arguments
}

Push-Location $ProjectRoot
try {
    if ($Target -in @("GUI", "Both")) {
        Invoke-PyInstallerBuild `
            -EntryScript "noir_search_gui.py" `
            -ExecutableName "noir_search" `
            -Windowed $true
    }

    if ($Target -in @("CLI", "Both")) {
        Invoke-PyInstallerBuild `
            -EntryScript "noir_search.py" `
            -ExecutableName "noir_search_cli" `
            -Windowed $false
    }

    foreach ($supportFile in @("config.json", "config.example.json", "queries.txt", "README.md")) {
        if (Test-Path -LiteralPath (Join-Path $ProjectRoot $supportFile)) {
            Copy-Item `
                -LiteralPath (Join-Path $ProjectRoot $supportFile) `
                -Destination $DistDir `
                -Force
        }
    }
}
finally {
    Pop-Location
}
