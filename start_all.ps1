# --- Configuration ---
$Project = "C:\Users\Administrator\Projets\martingale\scripts_startup"
$Tabs = @(
    @{Title = "1530A-1"; Script = "$Project\1530A-1.ps1"},
    @{Title = "5P40A-1"; Script = "$Project\5P40A-1.ps1"},
    @{Title = "4P6P-1"; Script = "$Project\4P6P-1.ps1"},
    @{Title = "BREAK-1"; Script = "$Project\BREAK-1.ps1"}
)

# --- Créer dossier logs s'il n'existe pas ---
$LogsFolder = "C:\Users\Administrator\Projets\martingale\logs"
if (-not (Test-Path $LogsFolder)) { New-Item -ItemType Directory -Path $LogsFolder }

# --- Lancer chaque onglet WT ---
$first = $true
foreach ($tab in $Tabs) {
    $arg = "new-tab --title `"$($tab.Title)`" powershell -NoExit -File `"$($tab.Script)`""

    if ($first) {
        Start-Process wt -ArgumentList $arg
        $first = $false
    } else {
        Start-Process wt -ArgumentList "-w 0 $arg"
    }
}
