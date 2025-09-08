# Requires: PowerShell 5+
$ErrorActionPreference = "Stop"

# Pasta do script
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Menu
Write-Host "Selecione o modo:" -ForegroundColor Cyan
Write-Host "1) Questão JFF (Autômato finito)"
Write-Host "2) Questões dissertativas / múltipla escolha (resposta sucinta)"
$choice = Read-Host "Digite 1 ou 2"

switch ($choice) {
	'1' { $env:ANSWER_MODE = 'fa' }
	'2' { $env:ANSWER_MODE = 'qa' }
	Default { $env:ANSWER_MODE = 'fa' }
}

# venv
if (-not (Test-Path ".venv/Scripts/python.exe")) {
	python -m venv .venv
}

# Depêndencias
& .\.venv\Scripts\python -m pip install --upgrade pip
& .\.venv\Scripts\python -m pip install -r requirements.txt

# Carregar .env se houver
$envPath = Join-Path $root ".env"
if (Test-Path $envPath) {
	$lines = Get-Content $envPath -Raw -ErrorAction SilentlyContinue
	$lines -split "`r?`n" | ForEach-Object {
		if ($_ -match "^([^#=]+)=(.*)$") {
			$name = $matches[1].Trim()
			$value = $matches[2].Trim()
			[System.Environment]::SetEnvironmentVariable($name, $value, "Process")
		}
	}
}

if (-not $env:GEMINI_API_KEY) {
	Write-Host "GEMINI_API_KEY não definida. Defina no .env ou no ambiente." -ForegroundColor Red
	exit 1
}

# Executar com FA por padrão e salvar JFFs por questão em out\resolvidas (se modo qa, ainda organiza por questão)
& .\.venv\Scripts\python -m src.main --in . --out out --type fa --solved-dir resolvidas

# Mostrar resultados
Write-Host "Arquivos em out/:" -ForegroundColor Cyan
Get-ChildItem -Force out | Select-Object Name, Length | Format-Table -AutoSize

Write-Host "Arquivos resolvidos (JFF por questão) em out\resolvidas/:" -ForegroundColor Cyan
Get-ChildItem -Force (Join-Path out resolvidas) -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize

# Copiar para a Área de Trabalho do usuário
try {
	$desktop = [Environment]::GetFolderPath('Desktop')
	$src = Join-Path $root 'out\\resolvidas'
	$dst = Join-Path $desktop 'resolvidas'
	if (Test-Path $src) {
		if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
		Copy-Item -Recurse -Force $src $dst
		Write-Host "Cópia concluída para: $dst" -ForegroundColor Green
	} else {
		Write-Host "Pasta de origem não encontrada: $src" -ForegroundColor Yellow
	}
} catch {
	Write-Host "Falha ao copiar para a Área de Trabalho: $($_.Exception.Message)" -ForegroundColor Red
}
