# --- Configuration ---
$Project = "C:\Users\Administrator\Projets\martingale\scripts_startup"
$Tabs = @(
    @{Title = "4315A-1"; Script = "$Project\4315A-1.ps1"},
    @{Title = "4030-1"; Script = "$Project\4030-1.ps1"},
    @{Title = "4015-1"; Script = "$Project\4015-1.ps1"},
    @{Title = "1SET-1"; Script = "$Project\1SET-1.ps1"}
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
