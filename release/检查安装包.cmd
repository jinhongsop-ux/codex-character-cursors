@echo off
setlocal
set "CURSOR_CHECK_SELF=%~f0"
set "CURSOR_CHECK_FLAGS=%*"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:CURSOR_CHECK_SELF,[Text.Encoding]::UTF8); Invoke-Expression $s.Substring($s.LastIndexOf('# POWERSHELL_PAYLOAD'))"
exit /b %errorlevel%
# POWERSHELL_PAYLOAD
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $env:CURSOR_CHECK_SELF
$quiet=$env:CURSOR_CHECK_FLAGS -match '--quiet'
try {
    $manifest=Get-Content -LiteralPath (Join-Path $root '文件清单.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach($file in $manifest.files){
        $path=Join-Path $root $file.path
        if(!(Test-Path -LiteralPath $path)){throw "缺少文件：$($file.path)"}
        $sha=[Security.Cryptography.SHA256]::Create()
        try{$hash=[BitConverter]::ToString($sha.ComputeHash([IO.File]::ReadAllBytes($path))).Replace('-','').ToLowerInvariant()}finally{$sha.Dispose()}
        if($hash -ne $file.sha256){throw "文件校验失败：$($file.path)"}
    }
    $message="安装包完整：V$($manifest.version)，五款角色、工作台和制作Skills均已通过校验。"
    Write-Output $message
    if(!$quiet){Add-Type -AssemblyName System.Windows.Forms;[void][System.Windows.Forms.MessageBox]::Show($message,'角色光标完整性检查')}
    exit 0
}catch{
    Write-Output $_.Exception.Message
    if(!$quiet){Add-Type -AssemblyName System.Windows.Forms;[void][System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'检查失败')}
    exit 1
}
