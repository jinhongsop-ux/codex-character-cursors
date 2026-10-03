@echo off
setlocal
set "CURSOR_SKILLS_SELF=%~f0"
set "CURSOR_SKILLS_FLAGS=%*"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:CURSOR_SKILLS_SELF,[Text.Encoding]::UTF8); Invoke-Expression $s.Substring($s.LastIndexOf('# POWERSHELL_PAYLOAD'))"
exit /b %errorlevel%
# POWERSHELL_PAYLOAD
$ErrorActionPreference='Stop'
try {
    $root=Split-Path -Parent $env:CURSOR_SKILLS_SELF
    $codexDirectory=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}
    $target=Join-Path $codexDirectory 'skills'
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    foreach($name in @('character-chibi-prep','character-cursor-state-designer','character-cursor-personality-designer','character-cursor-pack')){
        $source=Join-Path $root ('Skills/'+$name)
        if(!(Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))){throw "缺少Skill：$name，请完整解压安装包。"}
        Copy-Item -LiteralPath $source -Destination $target -Recurse -Force
    }
    Add-Type -AssemblyName System.Windows.Forms
    if($env:CURSOR_SKILLS_FLAGS -notmatch '--quiet'){[void][System.Windows.Forms.MessageBox]::Show("制作Skills已安装到：$target。请重新打开Codex使用。",'Skills安装完成')}
    exit 0
}catch{
    Add-Type -AssemblyName System.Windows.Forms
    if($env:CURSOR_SKILLS_FLAGS -notmatch '--quiet'){[void][System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'Skills安装失败')}
    Write-Output $_.Exception.Message
    exit 1
}
