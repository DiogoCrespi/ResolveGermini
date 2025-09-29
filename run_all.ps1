# Requires: PowerShell 5+
$ErrorActionPreference = "Stop"

# Seta as Politicas
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Pasta do script
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Garantir Python portátil em C:\Python313 se necessário
try {
	$portableSrc = Join-Path $root 'Python313'
	$portableDst = 'C:\\Python313'
	$dstExe = Join-Path $portableDst 'python.exe'
	if (-not (Test-Path $dstExe) -and (Test-Path $portableSrc)) {
		Write-Host "Instalando Python portátil em $portableDst" -ForegroundColor DarkGray
		if (-not (Test-Path $portableDst)) { New-Item -ItemType Directory -Path $portableDst -Force | Out-Null }
		Copy-Item -Recurse -Force $portableSrc\* $portableDst
	}
} catch {
	Write-Host "Aviso: não foi possível preparar C:\\Python313: $($_.Exception.Message)" -ForegroundColor Yellow
}

# venv (prioriza Python portátil local; só cai para PATH se não existir)
if (-not (Test-Path ".venv/Scripts/python.exe")) {
	$created = $false
	$localPy = Join-Path $root 'Python313\python.exe'
	if (Test-Path $localPy) {
		try {
			Write-Host "Criando venv com Python local: $localPy" -ForegroundColor DarkGray
			& $localPy -m venv .venv
			if (Test-Path ".venv/Scripts/python.exe") { $created = $true }
		} catch { }
	}
	if (-not $created) {
		$commands = @('python3', 'python', 'py -3', 'py')
		foreach ($cmd in $commands) {
			try {
				Write-Host "Tentando criar venv com: $cmd" -ForegroundColor DarkGray
				& $cmd -m venv .venv
				if (Test-Path ".venv/Scripts/python.exe") { $created = $true; break }
			} catch { }
		}
	}
	if (-not $created) {
		Write-Host "Não foi possível criar o ambiente virtual (.venv). Coloque um Python portátil em .\\Python313\\python.exe ou adicione python ao PATH." -ForegroundColor Red
		exit 1
	}
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

# Limpar pasta out e recriar out\resolvidas para reprocessamento completo
try {
	$outDir = Join-Path $root 'out'
	if (Test-Path $outDir) {
		Remove-Item -Recurse -Force $outDir
	}
	$resDir = Join-Path $outDir 'resolvidas'
	New-Item -ItemType Directory -Path $resDir -Force | Out-Null
} catch {
	Write-Host "Falha ao limpar/recriar out: $($_.Exception.Message)" -ForegroundColor Yellow
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
		# Copiar também utilitários para a pasta de destino
		try {
			$jflap = Join-Path $root 'JFLAP7.1.jar'
			if (Test-Path $jflap) { Copy-Item -Force $jflap (Join-Path $dst 'JFLAP7.1.jar') }
		} catch {}
		Write-Host "Cópia concluída para: $dst" -ForegroundColor Green
	} else {
		Write-Host "Pasta de origem não encontrada: $src" -ForegroundColor Yellow
	}
} catch {
	Write-Host "Falha ao copiar para a Área de Trabalho: $($_.Exception.Message)" -ForegroundColor Red
}
