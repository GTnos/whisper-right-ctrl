Option Explicit
Dim shell, fileSystem, environment, projectRoot, pythonw, application, command, exitCode
Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")
projectRoot = fileSystem.GetParentFolderName(WScript.ScriptFullName)
pythonw = projectRoot & "\.venv\Scripts\pythonw.exe"
application = projectRoot & "\src\whisper_right_ctrl\app.py"
Set environment = shell.Environment("Process")
environment("PYTHONPATH") = projectRoot & "\src"
environment("PATH") = projectRoot & "\.venv\Lib\site-packages\nvidia\cublas\bin;" & projectRoot & "\.venv\Lib\site-packages\nvidia\cudnn\bin;" & environment("PATH")
shell.CurrentDirectory = projectRoot
command = Chr(34) & pythonw & Chr(34) & " " & Chr(34) & application & Chr(34)
Do
    exitCode = shell.Run(command, 0, True)
    If exitCode = 75 Then
        WScript.Sleep 1500
    Else
        Exit Do
    End If
Loop
