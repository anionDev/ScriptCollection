foreach($sid in [System.Security.Principal.WindowsIdentity]::GetCurrent().Groups) { 
    Write-Host (($sid).Translate([System.Security.Principal.NTAccount]))
}