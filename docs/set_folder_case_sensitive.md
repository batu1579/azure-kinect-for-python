# Set Sase Sensitive For Folder

Use the following command first to check whether the folder currently needs to be set up:

```bash
fsutil.exe file queryCaseSensitiveInfo <path_to_folder>

# example
fsutil.exe file queryCaseSensitiveInfo D:\conda_env
```

If the display is disabled, you need to use the following instructions to set the folder to be case-sensitive

```bash
fsutil.exe file setCaseSensitiveInfo <path_to_folder>

# example
fsutil.exe file setCaseSensitiveInfo D:\conda_env enable
```
