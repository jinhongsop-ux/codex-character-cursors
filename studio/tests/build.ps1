$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$pkg=Join-Path $root 'package'
Copy-Item -LiteralPath (Join-Path $root 'web'),(Join-Path $root 'themes') -Destination $pkg -Recurse -Force
Copy-Item -LiteralPath (Join-Path $root 'assets/一键安装.cmd'),(Join-Path $root 'assets/一键恢复系统默认.cmd'),(Join-Path $root 'assets/一键恢复系统白色小号.cmd') -Destination $pkg -Force
& "$env:WINDIR\Microsoft.NET\Framework\v4.0.30319\csc.exe" /nologo /target:winexe /platform:anycpu "/out:$pkg\CursorStudio.exe" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll (Join-Path $root 'src/Studio.cs')
if($LASTEXITCODE -ne 0){throw 'Compile failed'}
[IO.File]::WriteAllText((Join-Path $pkg '启动光标工作台.cmd'),('@echo off'+"`r`n"+'start "" "%~dp0CursorStudio.exe"'+"`r`n"),[Text.Encoding]::ASCII)
