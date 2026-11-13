# Installation de l'environnement sous Windows (PowerShell)
# Usage : .\setup.ps1            -> dépendances communes
#         .\setup.ps1 -Module federated_learning | blockchain | traceability
param([string]$Module = "")
if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-common.txt
if ($Module -ne "") { pip install -r "$Module\requirements.txt" }
Write-Host "Environnement prêt. Lancez : pytest"
