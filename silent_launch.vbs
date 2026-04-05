Set WshShell = CreateObject("WScript.Shell")
' 這裡的路徑請換成你原本那個 .bat 檔的絕對路徑
WshShell.Run chr(34) & "C:\Users\user\Program\AI-todo-list\auto_launch.bat" & chr(34), 0
Set WshShell = Nothing