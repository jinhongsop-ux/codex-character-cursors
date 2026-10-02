param([string]$Version)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(!$Version){$Version=(Get-Content -LiteralPath (Join-Path $PSScriptRoot 'version.json') -Raw -Encoding UTF8 | ConvertFrom-Json).version}
if($Version -notmatch '^\d+\.\d+\.\d+$'){throw 'Version must be major.minor.patch'}
$staging=Join-Path $root ('.release-build/'+[Guid]::NewGuid().ToString('N'))
$name="角色光标完整合集-V$Version"
$package=Join-Path $staging $name
$output=Join-Path $root 'release-output'
New-Item -ItemType Directory -Path $package,$output -Force | Out-Null
foreach($dir in @('web','themes')){Copy-Item -LiteralPath (Join-Path $root ('studio/'+$dir)) -Destination $package -Recurse}
foreach($entry in @('一键安装.cmd','一键恢复系统默认.cmd','一键恢复系统白色小号.cmd')){
    Copy-Item -LiteralPath (Join-Path $root ('studio/assets/'+$entry)) -Destination $package
}
Copy-Item -LiteralPath (Join-Path $root 'skills') -Destination (Join-Path $package 'Skills') -Recurse
Copy-Item -LiteralPath (Join-Path $root 'previews/characters') -Destination (Join-Path $package '基础形象') -Recurse
Copy-Item -LiteralPath (Join-Path $PSScriptRoot '检查安装包.cmd'),(Join-Path $PSScriptRoot '安装制作Skills.cmd') -Destination $package
$utf8=New-Object Text.UTF8Encoding($false)
[IO.File]::WriteAllText((Join-Path $package '使用说明.txt'),([IO.File]::ReadAllText((Join-Path $PSScriptRoot '使用说明.txt')).Replace('__VERSION__',$Version)),$utf8)
[IO.File]::WriteAllText((Join-Path $package '启动光标工作台.cmd'),('@echo off'+"`r`n"+'start "" "%~dp0CursorStudio.exe"'+"`r`n"),[Text.Encoding]::ASCII)
$compiler=Join-Path $env:WINDIR 'Microsoft.NET/Framework/v4.0.30319/csc.exe'
& $compiler /nologo /target:winexe /platform:anycpu "/out:$package\CursorStudio.exe" /reference:System.Windows.Forms.dll /reference:System.Drawing.dll /reference:System.Web.Extensions.dll (Join-Path $root 'studio/src/Studio.cs')
if($LASTEXITCODE -ne 0){throw 'Compile failed'}
foreach($script in Get-ChildItem -LiteralPath $package -Filter '*.cmd' -Recurse){
    $text=[IO.File]::ReadAllText($script.FullName).Replace("`r`n","`n").Replace("`n","`r`n")
    [IO.File]::WriteAllText($script.FullName,$text,$utf8)
}
$catalog=Get-Content -LiteralPath (Join-Path $package 'themes/catalog.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if($catalog.Count -ne 5){throw 'Full release must contain five characters'}
foreach($theme in $catalog){foreach($role in $theme.roles){if(!(Test-Path -LiteralPath (Join-Path $package ('themes/'+$theme.id+'/'+$role.role+'.png')))){throw 'Missing role asset'}}}
$manifest=[ordered]@{version=$Version;themes=@($catalog.id);files=@()}
foreach($file in Get-ChildItem -LiteralPath $package -File -Recurse | Sort-Object FullName){
    $relative=$file.FullName.Substring($package.Length+1).Replace('\','/')
    $manifest.files+=@{path=$relative;bytes=$file.Length;sha256=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()}
}
[IO.File]::WriteAllText((Join-Path $package '文件清单.json'),($manifest | ConvertTo-Json -Depth 5),$utf8)
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip=Join-Path $output ($name+'.zip')
if(Test-Path -LiteralPath $zip){throw "Release already exists: $zip. Use a new version or move the previous build first."}
[IO.Compression.ZipFile]::CreateFromDirectory($package,$zip,[IO.Compression.CompressionLevel]::Optimal,$true)
$archive=[IO.Compression.ZipFile]::OpenRead($zip)
try{if(!($archive.Entries | Where-Object FullName -EQ ($name+'/CursorStudio.exe'))){throw 'ZIP executable missing'}}finally{$archive.Dispose()}
$hash=(Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash.ToLowerInvariant()
[IO.File]::WriteAllText((Join-Path $output 'SHA256SUMS.txt'),($hash+'  '+[IO.Path]::GetFileName($zip)+"`n"),$utf8)
Write-Output "Built $zip"
Write-Output "SHA256 $hash"
