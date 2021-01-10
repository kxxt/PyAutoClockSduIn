Remove-Item -r dist
Remove-Item release-nochrome.zip
pyinstaller clockin.spec
Copy-Item chromedriver.exe dist\
Copy-Item README.MD dist\README.MD
Copy-Item README.pdf dist\README.pdf
Copy-Item settings.json .\dist\
Set-Location dist
zip -9 -q ..\release-nochrome.zip .\*
Set-Location ..