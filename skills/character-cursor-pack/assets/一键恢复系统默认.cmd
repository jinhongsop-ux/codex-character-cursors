@echo off
setlocal
set "CURSOR_RESET_SELF=%~f0"
set "CURSOR_RESET_QUIET=%~1"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$s=[IO.File]::ReadAllText($env:CURSOR_RESET_SELF,[Text.Encoding]::UTF8); $p=$s.LastIndexOf('# POWERSHELL_PAYLOAD'); Invoke-Expression $s.Substring($p)"
exit /b %errorlevel%
# POWERSHELL_PAYLOAD
$ErrorActionPreference = 'Stop'
try {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class DefaultCursorNative {
 [DllImport("user32.dll", SetLastError=true)] public static extern bool SystemParametersInfoW(uint a,uint b,IntPtr c,uint d);
 [DllImport("user32.dll", CharSet=CharSet.Unicode, SetLastError=true)] public static extern IntPtr LoadImageW(IntPtr a,string b,uint c,int d,int e,uint f);
 [DllImport("user32.dll", SetLastError=true)] public static extern bool SetSystemCursor(IntPtr h,uint id);
 [DllImport("user32.dll")] public static extern bool DestroyCursor(IntPtr h);
 [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern IntPtr SendMessageTimeoutW(IntPtr h,uint m,IntPtr w,string l,uint f,uint t,out IntPtr r);
}
"@
    $roles = @(
        @('Arrow','aero_arrow.cur',32512), @('Help','aero_helpsel.cur',32651),
        @('AppStarting','aero_working.ani',32650), @('Wait','aero_busy.ani',32514),
        @('Crosshair','cross_r.cur',32515), @('IBeam','beam_r.cur',32513),
        @('NWPen','aero_pen.cur',32631), @('No','aero_unavail.cur',32648),
        @('SizeAll','aero_move.cur',32646), @('SizeWE','aero_ew.cur',32644),
        @('SizeNESW','aero_nesw.cur',32643), @('UpArrow','aero_up.cur',32516),
        @('SizeNS','aero_ns.cur',32645), @('SizeNWSE','aero_nwse.cur',32642),
        @('Hand','aero_link.cur',32649), @('Pin','aero_pin.cur',32671),
        @('Person','aero_person.cur',32672)
    )
    foreach ($role in $roles) {
        $path = Join-Path $env:SystemRoot ('Cursors\' + $role[1])
        # Older Windows releases may not have the last two roles.
        if (!(Test-Path -LiteralPath $path) -and $role[0] -notin @('Pin','Person')) { throw "缺少系统光标文件：$path" }
    }
    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('Control Panel\Cursors')
    try {
        foreach ($role in $roles) {
            $value = '%SystemRoot%\Cursors\' + $role[1]
            if (!(Test-Path -LiteralPath ([Environment]::ExpandEnvironmentVariables($value)))) { $value = '' }
            $key.SetValue($role[0],$value,[Microsoft.Win32.RegistryValueKind]::ExpandString)
        }
        $key.SetValue('','Windows Aero',[Microsoft.Win32.RegistryValueKind]::String)
        $key.SetValue('Scheme Source',2,[Microsoft.Win32.RegistryValueKind]::DWord)
        $key.SetValue('CursorBaseSize',32,[Microsoft.Win32.RegistryValueKind]::DWord)
    } finally { $key.Dispose() }
    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey('SOFTWARE\Microsoft\Accessibility')
    try {
        $key.SetValue('CursorSize',1,[Microsoft.Win32.RegistryValueKind]::DWord)
        $key.SetValue('CursorType',0,[Microsoft.Win32.RegistryValueKind]::DWord)
        $key.SetValue('CursorColor',0xffffff,[Microsoft.Win32.RegistryValueKind]::DWord)
    } finally { $key.Dispose() }
    $result = [IntPtr]::Zero
    foreach ($section in @('Control Panel\Cursors','SOFTWARE\Microsoft\Accessibility')) {
        [void][DefaultCursorNative]::SendMessageTimeoutW([IntPtr]0xffff,0x1a,[IntPtr]::Zero,$section,2,1000,[ref]$result)
    }
    if (![DefaultCursorNative]::SystemParametersInfoW(0x57,0,[IntPtr]::Zero,0)) { throw 'Windows 未能重新加载默认光标。' }
    foreach ($role in $roles) {
        $path = Join-Path $env:SystemRoot ('Cursors\' + $role[1])
        if (!(Test-Path -LiteralPath $path)) { continue }
        $handle = [DefaultCursorNative]::LoadImageW([IntPtr]::Zero,$path,2,32,32,0x10)
        if ($handle -eq [IntPtr]::Zero) { throw "无法加载默认光标：$($role[0])" }
        if (![DefaultCursorNative]::SetSystemCursor($handle,$role[2])) {
            [void][DefaultCursorNative]::DestroyCursor($handle)
            # Pin and Person are unavailable on some Windows versions.
            if ($role[0] -notin @('Pin','Person')) { throw "无法应用默认光标：$($role[0])" }
        }
    }
    Write-Output '已恢复 Windows 默认白色光标和默认大小（大小滑块为 1）。'
    if ($env:CURSOR_RESET_QUIET -ne '--quiet') {
        Add-Type -AssemblyName System.Windows.Forms
        [void][System.Windows.Forms.MessageBox]::Show('已恢复 Windows 默认白色光标和默认大小。此文件可用于任何角色光标包。','恢复系统默认')
    }
    exit 0
} catch {
    Write-Output $_.Exception.Message
    if ($env:CURSOR_RESET_QUIET -ne '--quiet') {
        Add-Type -AssemblyName System.Windows.Forms
        [void][System.Windows.Forms.MessageBox]::Show($_.Exception.Message,'恢复失败')
    }
    exit 1
}
