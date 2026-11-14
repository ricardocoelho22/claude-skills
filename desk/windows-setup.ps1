# Windows side of the desk box. The WSL distro is named "Ubuntu" (check: wsl -l -v).
# Copy and paste one block at a time into
# PowerShell as admin. Context: desk/README.md
#
# To open this file from Windows, paste this into Explorer's address bar or
# Notepad's Open dialog:
#   \\wsl.localhost\Ubuntu\home\ricardo\Code\claude-skills\desk\windows-setup.ps1


# --- 1. WSL limits (.wslconfig). Already in place: only needed for a rebuild ---

@'
[wsl2]
memory=24GB
processors=14
swap=8GB
swapFile=E:\\WSL\\swap.vhdx
vmIdleTimeout=-1

[experimental]
autoMemoryReclaim=gradual
'@ | Set-Content -Path "$env:USERPROFILE\.wslconfig" -Encoding ascii
wsl --shutdown


# --- 2. Keep WSL running after you log in to Windows (no window) -------------

$a = New-ScheduledTaskAction -Execute "conhost.exe" -Argument "--headless wsl.exe -d Ubuntu --exec sleep infinity"
$t = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$s = New-ScheduledTaskSettingsSet -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "WSL keep-alive" -Action $a -Trigger $t -Settings $s -Force
Start-ScheduledTask -TaskName "WSL keep-alive"

# Check it worked: State should say Running
Get-ScheduledTask -TaskName "WSL keep-alive" | Select-Object TaskName, State


# --- 3. Day to day -----------------------------------------------------------

wsl -l -v                                        # is Ubuntu running?
wsl --shutdown                                   # free all WSL memory (kills tmux and agent sessions)
Start-ScheduledTask -TaskName "WSL keep-alive"   # start WSL again, without a window


# --- 4. Maintenance (admin) --------------------------------------------------

# Shrink the virtual disk after deleting a lot inside Ubuntu:
wsl --shutdown
diskpart
#   then type, one line at a time:
#   select vdisk file="E:\WSL\Ubuntu\ext4.vhdx"
#   compact vdisk
#   exit

# Move Ubuntu to another drive (replace X):
wsl --shutdown
wsl --manage Ubuntu --move X:\WSL\Ubuntu

# Remove the keep-alive task:
Unregister-ScheduledTask -TaskName "WSL keep-alive" -Confirm:$false
