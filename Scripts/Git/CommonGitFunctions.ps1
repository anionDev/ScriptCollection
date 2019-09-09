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
    $changedFiles=$stdout.Split([Environment]::NewLine) | Where-Object { $_ -ne "" }
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
                throw [System.Exception] "'Git diff $_' had exitcode $exitCode"
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
function GetAllRemotes($repositoryFolder){
    $originalWorkingDirectory=(Get-Item -Path ".\").FullName
    try{
        cd $repositoryFolder
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "git"
        $pinfo.RedirectStandardError = $true
        $pinfo.RedirectStandardOutput = $true
        $pinfo.WorkingDirectory=$repositoryFolder
        $pinfo.UseShellExecute = $false
        $pinfo.Arguments = "remote"
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo
        $p.Start() | Out-Null
        $p.WaitForExit()
        $exitCode=$p.ExitCode
        if($exitCode -ne 0){
            throw [System.Exception] "'Git remote' had exitcode $exitCode"
        }
        $remotes = $p.StandardOutput.ReadToEnd()
        $listCollection = New-Object 'Collections.Generic.List[string]'
        $splitted=$remotes.split([Environment]::NewLine)
        ForEach($splittedItem in $splitted){
            if($splittedItem -ne ""){
                $listCollection.Add($splittedItem)
            }
        }
        return $listCollection
    }
    finally{
        cd $originalWorkingDirectory
    }
}
function RemoveAllRemotes($repositoryFolder){
    $originalWorkingDirectory=(Get-Item -Path ".\").FullName
    try{
        cd $repositoryFolder
        ForEach($remote in GetAllRemotes($repositoryFolder)){
            $pinfo = New-Object System.Diagnostics.ProcessStartInfo
            $pinfo.FileName = "git"
            $pinfo.RedirectStandardError = $true
            $pinfo.RedirectStandardOutput = $true
            $pinfo.WorkingDirectory=$repositoryFolder
            $pinfo.UseShellExecute = $false
            $pinfo.Arguments = "remote remove $remote"
            $p = New-Object System.Diagnostics.Process
            $p.StartInfo = $pinfo
            $p.Start() | Out-Null
            $p.WaitForExit()
            $exitCode=$p.ExitCode
            if($exitCode -ne 0){
                throw [System.Exception] "'Git remote remove $remote' had exitcode $exitCode"
            }
        }
    }
    finally{
        cd $originalWorkingDirectory
    }
}
function RepositoryHasUncommittedChanges($repositoryFolder){
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = "git"
    $pinfo.WorkingDirectory=$repositoryFolder
    $pinfo.UseShellExecute = $false
    $pinfo.Arguments = "git diff-index --quiet HEAD --"
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo = $pinfo
    $p.Start()
    $p.WaitForExit()
    $exitCode=$p.ExitCode
    return $exitCode -ne 0
}

function PullFastForwardIfThereAreNoUncommittedChanges($repositoryFolder, $remote){
    cd $repositoryFolder
    if(-Not (RepositoryHasUncommittedChanges($repositoryFolder))){
        $pinfo = New-Object System.Diagnostics.ProcessStartInfo
        $pinfo.FileName = "git"
        $pinfo.WorkingDirectory=$repositoryFolder
        $pinfo.UseShellExecute = $false
        $pinfo.Arguments = "pull --ff-only $remote"
        $p = New-Object System.Diagnostics.Process
        $p.StartInfo = $pinfo
        $p.Start()
        $p.WaitForExit()
        $exitCode=$p.ExitCode
        if($exitCode -ne 0){
            throw [System.Exception] "'Git pull --ff-only $remote' had exitcode $exitCode"
        }
        return true
    }else{
        return false
    }
}
