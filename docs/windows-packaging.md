# Windows Packaging

Run `scripts\package_release.bat` from a Python 3.12 development environment with Inno Setup 6 installed.

The production package remains one-folder for reliable Qt plugin, keyring, resource, and plugin discovery behavior. The installer is written to:

`dist/installer/Vegas_Total_Solution_Doc_Setup.exe`

The build uses the checked-in PyInstaller spec, performs conservative Qt runtime cleanup, compiles with Inno Setup LZMA2 ultra64 solid compression, and writes `artifacts/package_size_after.txt`.

GitHub Actions builds both the unoptimized baseline and optimized package in the same Windows job, runs tests, performs a frozen startup smoke check, and uploads the installer plus package size reports.
