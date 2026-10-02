# Windows packaging and recovery

## Installation invariants

Use current-user paths and OS-provided runtime dependencies; no development tools or network should be needed by the recipient. Avoid hardcoded author usernames, drives, source paths and fixed Windows directory names. Package the installer executable and all needed role assets together. Chinese names and spaces must work after extraction.

Back up the first pre-install configuration once, preserving registry value types and absent values. Include all role paths, scheme identity/source, CursorBaseSize and accessibility size/type/color when changed by installation. Do not overwrite the original on repeated install. For doubled-size installs, derive size from the preserved baseline once rather than the active enlarged size. Verify available CUR frames satisfy the intended display size and scaling limits.

Do not equate scheme paths with active cursor dimensions. Windows scheme reload may replace live sizes. Inspect real handles after applying; release owned handles correctly. SetSystemCursor consumes the cursor handle on success. Handle missing Pin/Person support on older systems without claiming those roles were applied.

## Universal reset assets

`../assets/一键恢复系统默认.cmd` and `../assets/一键恢复系统白色小号.cmd` are self-contained batch files with embedded PowerShell/C# using Windows APIs. They depend on Windows PowerShell/.NET, not a theme EXE, assets or a backup. They reset accessibility CursorSize=1, CursorType=0 and CursorColor=white; set system role paths using SystemRoot; apply Windows Aero scheme and clear enlarged CursorBaseSize. Standard reset uses32, small reset24. Their --quiet argument supports unattended checks without a dialog.

For the V1.5 delivery profile, copy the small file as `一键恢复原状.cmd`. Keep `恢复安装前配置.cmd` explicitly backup-based. Do not silently make the small reset restore a saved yellow or enlarged cursor. Reset does not delete files.

The small reset currently reapplies24 to live handles; Windows SPI_SETCURSORS reload can return active cursors to32. Document this limitation prominently in usage instructions and completion messages where relevant. Do not add a background service, startup task or persistence mechanism without a user request.

When editing these polyglot CMD files, save UTF-8 without BOM and Windows CRLF line endings. The ASCII batch bootstrap reads its own UTF-8 payload through an environment path and LastIndexOf payload marker. LF-only or BOM-bearing batch files have failed in this environment. Do not run the payload as raw cmd statements. Use SPI_SETCURSORS with flags0; flags3 failed on the tested machine.

## Verification and archive

Meaningful checks: install/reinstall baseline does not drift; all supported live role dimensions match requested size; white arrow pixels/hotspot match an OS default loaded at that size; accessibility registry is reset; repeated reset works; scheme reload behavior is accurately reported. Include monochrome handles in dimension checks: without a color bitmap, mask bitmap height is twice the cursor height. Animated busy/working frames vary, so avoid requiring one frame hash to remain constant.

If Python via a WindowsApps alias reports settings inconsistent with native PowerShell, verify with the actual native Python executable or a native registry probe before drawing conclusions; an alias yielded divergent registry reads here.

Build a fresh release ZIP with required root files and direct cursor assets; exclude stale diagnostic renders and test executables. Open the final archive and verify the actual Chinese entries and UTF-8 usage text. Keep previous release files unless asked otherwise. Include a checksum for distribution when useful. Only report tests performed; lack of testing on other computers is not proof of incompatibility or compatibility.
