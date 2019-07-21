trap {
  Throw $_
  exit
}

$launcher = "python3\python.exe"
if (!(Test-Path $launcher)) {
    $url = "https://www.python.org/ftp/python/3.7.3/python-3.7.3-embed-amd64.zip"
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Write-Output "Downloading..."
    (New-Object System.Net.WebClient).DownloadFile($url, "python3.zip")
    $url = "https://bootstrap.pypa.io/get-pip.py"
    (New-Object System.Net.WebClient).DownloadFile($url, "get-pip.py")
    $progressPreference = 'silentlyContinue'
    Expand-Archive python3.zip -DestinationPath python3
    # Remove-Item "python3.zip"
    & $launcher bootstrap.py
}
# & $launcher website.py launch 9001 --open
& $launcher website.py launch 9001
