@echo off
setlocal
set "STUDIO_INSTALL_SELF=%~f0"
set "STUDIO_INSTALL_FLAGS=%*"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:STUDIO_INSTALL_SELF,[Text.Encoding]::UTF8); $p=$s.LastIndexOf('# POWERSHELL_PAYLOAD'); Invoke-Expression $s.Substring($p)"
exit /b %errorlevel%
# POWERSHELL_PAYLOAD
$ErrorActionPreference='Stop'
$source=Split-Path -Parent $env:STUDIO_INSTALL_SELF
$homePath=Join-Path $env:LOCALAPPDATA 'CharacterCursorStudio'
$target=Join-Path $homePath 'app'
$quiet=$env:STUDIO_INSTALL_FLAGS -match '--quiet'
$noLaunch=$env:STUDIO_INSTALL_FLAGS -match '--no-launch'
try {
    foreach($relative in @('CursorStudio.exe','web\index.html','web\app.js','web\style.css','themes\catalog.json','一键恢复系统默认.cmd','一键恢复系统白色小号.cmd')) {
        if (!(Test-Path -LiteralPath (Join-Path $source $relative))) {throw "安装文件不完整：$relative。请完整解压安装包后再运行。"}
    }
    $catalog=Get-Content -LiteralPath (Join-Path $source 'themes\catalog.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach($theme in $catalog) {foreach($role in $theme.roles) {
        $asset=Join-Path $source ('themes\'+$theme.id+'\'+$role.role+'.png')
        if (!(Test-Path -LiteralPath $asset)) {throw "缺少角色素材：$($theme.id)/$($role.role)"}
    }}
    Add-Type -AssemblyName System.Windows.Forms
    New-Item -ItemType Directory -Path $homePath -Force | Out-Null
    # Stop only the recorded Studio process after verifying its executable identity.
    $sessionFile=Join-Path $homePath 'session.json'
    if(Test-Path -LiteralPath $sessionFile) {
        $session=Get-Content -LiteralPath $sessionFile -Raw -Encoding UTF8 | ConvertFrom-Json
        $existing=Get-Process -Id $session.pid -ErrorAction SilentlyContinue
        if($existing -and $existing.ProcessName -eq 'CursorStudio' -and [IO.Path]::GetFileName($existing.Path) -eq 'CursorStudio.exe') {
            Stop-Process -Id $existing.Id -ErrorAction Stop
            $existing.WaitForExit(5000) | Out-Null
        }
    }
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    if([IO.Path]::GetFullPath($source).TrimEnd('\') -ne [IO.Path]::GetFullPath($target).TrimEnd('\')) {
        foreach($name in @('CursorStudio.exe','web','themes','使用说明.txt','VERIFIED.txt','启动光标工作台.cmd','一键恢复系统默认.cmd','一键恢复系统白色小号.cmd','一键安装.cmd')) {
            $item=Join-Path $source $name
            if(Test-Path -LiteralPath $item) {Copy-Item -LiteralPath $item -Destination $target -Recurse -Force}
        }
    }
    $shortcutPath=Join-Path ([Environment]::GetFolderPath('Programs')) '角色光标工作台.lnk'
    $shell=New-Object -ComObject WScript.Shell
    $shortcut=$shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath=Join-Path $target 'CursorStudio.exe'
    $shortcut.WorkingDirectory=$target
    $shortcut.Description='角色光标工作台：调整大小、应用皮肤、恢复系统光标'
    $shortcut.Save()
    $result="安装完成：$target`r`n可从开始菜单打开[角色光标工作台]。网页中选择角色后点击[应用到系统]。"
    [IO.File]::WriteAllText((Join-Path $homePath 'install-log.txt'),$result,[Text.Encoding]::UTF8)
    Write-Output $result
    if(!$noLaunch) {Start-Process -FilePath (Join-Path $target 'CursorStudio.exe') -WorkingDirectory $target -WindowStyle Hidden}
    exit 0
} catch {
    New-Item -ItemType Directory -Path $homePath -Force | Out-Null
    $errorText="安装失败：$($_.Exception.Message)`r`n日志：$(Join-Path $homePath 'install-log.txt')"
    [IO.File]::WriteAllText((Join-Path $homePath 'install-log.txt'),$errorText,[Text.Encoding]::UTF8)
    Write-Output $errorText
    if(!$quiet) {Add-Type -AssemblyName System.Windows.Forms;[void][System.Windows.Forms.MessageBox]::Show($errorText,'角色光标工作台安装失败')}
    exit 1
}
