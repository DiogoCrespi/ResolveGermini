# Requires: PowerShell 5+
$ErrorActionPreference = "Stop"

# Pasta do script
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

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

# Executar modo único: FA (gera JFF) e salvar JFFs por questão em out\resolvidas
& .\.venv\Scripts\python -m src.main --in . --out out --type fa --solved-dir resolvidas

# Renomear JFFs em out\resolvidas para nomes curtos (Q1a, Q1b, Q2a...)
$resolvedDir = Join-Path out resolvidas
if (Test-Path $resolvedDir) {
	Get-ChildItem -File (Join-Path $resolvedDir "*.jff") -ErrorAction SilentlyContinue | ForEach-Object {
		$name = $_.Name
		if ($name -match "_(Q[0-9]+[a-z]?)\.jff$") {
			$new = "$($Matches[1]).jff"
			if ($name -ne $new) {
				Rename-Item -Path $_.FullName -NewName $new -Force
			}
		}
	}
}

# Mostrar resultados
Write-Host "Arquivos em out/:" -ForegroundColor Cyan
Get-ChildItem -Force out | Select-Object Name, Length | Format-Table -AutoSize

Write-Host "Arquivos resolvidos (JFF por questão) em out\resolvidas/:" -ForegroundColor Cyan
Get-ChildItem -Force (Join-Path out resolvidas) -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize

# Copiar para a Área de Trabalho do usuário
try {
	$desktop = [Environment]::GetFolderPath('Desktop')
	$src = Join-Path $root 'out\resolvidas'
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
