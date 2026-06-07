# AI智能数据分析系统 - 一键启动脚本 (PowerShell版)
# 使用方式: 右键 -> 使用PowerShell运行 或 .\start.ps1

param(
    [switch]$NoBrowser,    # 不自动打开浏览器
    [switch]$KeepOpen      # 保持窗口打开
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) { $ProjectRoot = Get-Location }

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AI智能数据分析系统 启动器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "[1/4] 检查Python环境..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   错误: 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

# 检查依赖
Write-Host "[2/4] 检查依赖包..." -ForegroundColor Yellow
$requiredPackages = @("fastapi", "uvicorn", "pandas", "openpyxl", "langchain", "langchain-community", "pydantic")
foreach ($pkg in $requiredPackages) {
    $installed = python -c "import $($pkg -replace '-', '_')" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   正在安装缺失的包: $pkg" -ForegroundColor Yellow
        pip install $pkg --quiet 2>&1 | Out-Null
    }
}
Write-Host "   依赖检查完成" -ForegroundColor Green

# 检查.env配置
Write-Host "[3/4] 检查配置文件..." -ForegroundColor Yellow
$envFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "   警告: .env配置文件不存在" -ForegroundColor Yellow
} else {
    Write-Host "   .env配置文件已找到" -ForegroundColor Green
}

# 创建日志目录
$logsDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Path $logsDir | Out-Null
}

# 启动后端服务
Write-Host "[4/4] 启动后端服务..." -ForegroundColor Yellow
Write-Host ""

$backendLog = Join-Path $logsDir "backend.log"

# 使用Start-Process启动后端
$backendProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $ProjectRoot `
    -PassThru `
    -NoNewWindow

# 等待服务启动
Start-Sleep -Seconds 4

# 检查后端是否成功启动
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Host ""
    Write-Host "   后端服务已启动 (PID: $($backendProcess.Id))" -ForegroundColor Green
    Write-Host "   API地址: http://localhost:8000" -ForegroundColor Cyan
} else {
    Write-Host ""
    Write-Host "   警告: 端口8000未被占用，服务可能未正常启动" -ForegroundColor Yellow
    Write-Host "   请检查日志: $backendLog" -ForegroundColor Yellow
}

# 打开浏览器
if (-not $NoBrowser) {
    Write-Host ""
    Write-Host "正在打开浏览器..." -ForegroundColor Yellow
    Start-Process "http://localhost:8000"
}

# 显示访问提示
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   系统已就绪!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "   访问地址:" -ForegroundColor White
Write-Host "     前端页面: http://localhost:8000" -ForegroundColor Cyan
Write-Host "     API文档:   http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "   按 Ctrl+C 停止服务" -ForegroundColor White
Write-Host ""

# 如果使用-KeepOpen参数，保持窗口
if ($KeepOpen) {
    Write-Host "窗口保持打开状态..." -ForegroundColor Gray
    while ($true) { Start-Sleep -Seconds 1 }
}

# 等待后端进程退出
try {
    Wait-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
} catch {
    # 用户中断或进程结束
}

# 清理
Write-Host ""
Write-Host "正在停止服务..." -ForegroundColor Yellow
if (-not $backendProcess.HasExited) {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
}
Write-Host "服务已停止" -ForegroundColor Green
