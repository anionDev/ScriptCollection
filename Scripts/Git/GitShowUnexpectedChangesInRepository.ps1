function ShowUnexpectedChangesInGitRepository($repositoryFolder, $expectedChanges){
	$sourceFolder= $repositoryFolder
	$expectedChangesList=$expectedChanges
	$pinfo = New-Object System.Diagnostics.ProcessStartInfo
	$pinfo.FileName = "git"
	$pinfo.RedirectStandardError = $true
	$pinfo.RedirectStandardOutput = $true
	$pinfo.WorkingDirectory=$sourceFolder
	$pinfo.UseShellExecute = $false
	$pinfo.Arguments = "diff --name-only"
	$p = New-Object System.Diagnostics.Process
	$p.StartInfo = $pinfo
	$p.Start() | Out-Null
	$p.WaitForExit()
	$exitCode=$p.ExitCode
	if($exitCode -ne 0){
		Write-Host "'Git diff --name-only' had exitcode $exitCode"
		Exit $exitCode
	}
	$stdout = $p.StandardOutput.ReadToEnd()
	$changedFiles=$stdout.Split([Environment]::NewLine) | Where-Object { $_ –ne "" }
	$repositoryHasUnexpectedChanges=$false
	$changedFiles | ForEach-Object {
		if(-Not $expectedChanges.Contains($_)){
			$repositoryHasUnexpectedChanges=$true
			$pinfo = New-Object System.Diagnostics.ProcessStartInfo
			$pinfo.FileName = "git"
			$pinfo.RedirectStandardError = $true
			$pinfo.RedirectStandardOutput = $true
			$pinfo.WorkingDirectory=$sourceFolder
			$pinfo.UseShellExecute = $false
			$pinfo.Arguments = "diff $_"
			$p = New-Object System.Diagnostics.Process
			$p.StartInfo = $pinfo
			$p.Start() | Out-Null
			$p.WaitForExit()
			$exitCode=$p.ExitCode
			if($exitCode -ne 0){
				Write-Host "'Git diff $_' had exitcode $exitCode"
				Exit $exitCode
			}
			$stdout = $p.StandardOutput.ReadToEnd()
			Write-Host "Unexpected change in file '$_' :"
			Write-Host $stdout

		}
	}
	if($repositoryHasUnexpectedChanges){
		return 1
	}else{
		return 0
	}
}