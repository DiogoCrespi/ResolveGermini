# Requires: PowerShell 5+
$ErrorActionPreference = "Stop"

# Seta as Politicas
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Pasta do script
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

# Garantir Python portatil em C:\Python313 se necessario
try {
	$portableSrc = Join-Path $root 'Python313'
	$portableDst = 'C:\\Python313'
	$dstExe = Join-Path $portableDst 'python.exe'
	if (-not (Test-Path $dstExe) -and (Test-Path $portableSrc)) {
		Write-Host "Instalando Python portatil em $portableDst" -ForegroundColor DarkGray
		if (-not (Test-Path $portableDst)) { New-Item -ItemType Directory -Path $portableDst -Force | Out-Null }
		Copy-Item -Recurse -Force $portableSrc\* $portableDst
	}
} catch {
		Write-Host "Aviso: nao foi possivel preparar C:\\Python313: $($_.Exception.Message)" -ForegroundColor Yellow
}

# venv (prioriza Python portatil local; so cai para PATH se nao existir)
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
		Write-Host "Nao foi possivel criar o ambiente virtual (.venv). Coloque um Python portatil em .\\Python313\\python.exe ou adicione python ao PATH." -ForegroundColor Red
		exit 1
	}
}

# Dependencias
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

# Configuracoes de otimizacao (podem ser sobrescritas pelo .env)
if (-not $env:MAX_PARALLEL_WORKERS) {
    [System.Environment]::SetEnvironmentVariable("MAX_PARALLEL_WORKERS", "4", "Process")
}
if (-not $env:ENABLE_DESKTOP_COPY) {
    [System.Environment]::SetEnvironmentVariable("ENABLE_DESKTOP_COPY", "true", "Process")
}

# Verificar se pelo menos uma chave de API esta definida
$aiModel = if ($env:AI_MODEL) { $env:AI_MODEL.ToLower() } else { "gemini" }

if ($aiModel -eq "gpt") {
	if (-not $env:OPENAI_API_KEY) {
		Write-Host "AI_MODEL=gpt mas OPENAI_API_KEY nao definida. Defina no .env ou no ambiente." -ForegroundColor Red
		exit 1
	}
	Write-Host "Usando ChatGPT (modelo: $($env:GPT_MODEL))" -ForegroundColor Green
} elseif ($aiModel -eq "deepseek") {
	if (-not $env:DEEPSEEK_API_KEY) {
		Write-Host "AI_MODEL=deepseek mas DEEPSEEK_API_KEY nao definida. Defina no .env ou no ambiente." -ForegroundColor Red
		exit 1
	}
	Write-Host "Usando DeepSeek (modelo: $($env:DEEPSEEK_MODEL))" -ForegroundColor Green
} elseif ($aiModel -eq "gemini") {
	if (-not $env:GEMINI_API_KEY) {
		Write-Host "AI_MODEL=gemini mas GEMINI_API_KEY nao definida. Defina no .env ou no ambiente." -ForegroundColor Red
		exit 1
	}
        Write-Host "Usando Gemini (modelo: $($env:GEMINI_MODEL))" -ForegroundColor Green
    } else {
        Write-Host "AI_MODEL deve ser 'gemini', 'gpt' ou 'deepseek'. Valor atual: $aiModel" -ForegroundColor Red
        exit 1
    }

# Mostrar configuracoes de otimizacao
Write-Host "`n Configuracoes de Otimizacao:" -ForegroundColor Cyan
Write-Host "   Threads paralelas: $($env:MAX_PARALLEL_WORKERS)" -ForegroundColor White
Write-Host "   Copia para area de trabalho: $($env:ENABLE_DESKTOP_COPY)" -ForegroundColor White
Write-Host "   Rate limit: $($env:RATE_LIMIT_PER_MINUTE) req/min" -ForegroundColor White

# Limpar pasta Desktop/resolvidas de forma agressiva (primeira coisa)
try {
	$desktop = [Environment]::GetFolderPath('Desktop')
	$desktopResolvidas = Join-Path $desktop 'resolvidas'
	if (Test-Path $desktopResolvidas) {
		Write-Host "Limpando pasta Desktop/resolvidas..." -ForegroundColor Yellow
		# Forca remocao mesmo com arquivos em uso
		Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $desktopResolvidas
		# Aguarda um pouco e tenta novamente se ainda existir
		Start-Sleep -Milliseconds 500
		if (Test-Path $desktopResolvidas) {
			Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $desktopResolvidas
		}
		Write-Host "Pasta Desktop/resolvidas limpa com sucesso" -ForegroundColor Green
	}
} catch {
		Write-Host "Aviso: Nao foi possivel limpar Desktop/resolvidas: $($_.Exception.Message)" -ForegroundColor Yellow
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

# Criar pasta Desktop/resolvidas e copiar JFLAP7.1.jar de primeira
try {
	$desktop = [Environment]::GetFolderPath('Desktop')
	$desktopResolvidas = Join-Path $desktop 'resolvidas'
	if (-not (Test-Path $desktopResolvidas)) {
		New-Item -ItemType Directory -Path $desktopResolvidas -Force | Out-Null
	}
	$jflap = Join-Path $root 'JFLAP7.1.jar'
	if (Test-Path $jflap) {
		Copy-Item -Force $jflap (Join-Path $desktopResolvidas 'JFLAP7.1.jar')
		Write-Host "JFLAP7.1.jar copiado para Desktop/resolvidas" -ForegroundColor Green
	}
} catch {
		Write-Host "Aviso: Nao foi possivel copiar JFLAP7.1.jar: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Executar modo unico: FA (gera JFF) e salvar JFFs por questao em out\resolvidas
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

Write-Host "Arquivos resolvidos (JFF por questao) em out\resolvidas/:" -ForegroundColor Cyan
Get-ChildItem -Force (Join-Path out resolvidas) -ErrorAction SilentlyContinue | Select-Object Name, Length | Format-Table -AutoSize

# Copiar para a Area de Trabalho do usuario (sem limpar arquivos ja copiados)
try {
	$desktop = [Environment]::GetFolderPath('Desktop')
	$src = Join-Path $root 'out\resolvidas'
	$dst = Join-Path $desktop 'resolvidas'
	if (Test-Path $src) {
		# Criar pasta de destino se nao existir (sem limpar arquivos existentes)
		if (-not (Test-Path $dst)) { 
			New-Item -ItemType Directory -Path $dst -Force | Out-Null
		}
		
		# Copiar apenas arquivos que nao existem ou sao mais novos
		Copy-Item -Recurse -Force $src $dst
		
	# Copiar tambem utilitarios para a pasta de destino
	try {
		$jflap = Join-Path $root 'JFLAP7.1.jar'
		if (Test-Path $jflap) { Copy-Item -Force $jflap (Join-Path $dst 'JFLAP7.1.jar') }
	} catch {}
	Write-Host "Copia concluida para: $dst" -ForegroundColor Green
} else {
	Write-Host "Pasta de origem nao encontrada: $src" -ForegroundColor Yellow
}
} catch {
	Write-Host "Falha ao copiar para a Area de Trabalho: $($_.Exception.Message)" -ForegroundColor Red
}
