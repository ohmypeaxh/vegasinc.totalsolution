# Windows packaging

Run on Windows with Python 3.12 using scripts\\setup_dev.bat and scripts\\package_release.bat.

The production runtime is a PyInstaller one-folder build. Vegas_Total_Solution_Doc.spec
keeps the Qt Core/Gui/Widgets stack, HTTP support, image formats, PyMuPDF binaries,
python-docx, requests, and Windows keyring support. It excludes only confirmed-unused
optional Qt modules and development/test packages. UPX remains disabled because Qt DLL
compression can cause startup and antivirus issues.

The installer uses Inno Setup 6 with Compression=lzma2/ultra64,
SolidCompression=yes, and LZMAUseSeparateProcess=yes.

GitHub Actions runs all tests, builds the optimized spec, compiles Inno Setup, writes
`artifacts/package_size_after.txt`, and uploads the installer, checksums, and build manifest.
The preferred target is 100 MB or less, with warnings above 100 MB and 120 MB and a hard
failure above 160 MB. No package size is estimated before the Windows run completes.

The release artifact is dist/installer/Vegas_Total_Solution_Doc_Setup.exe.

The installer uses `C:\Program Files\Vegas Inc\Vegas Total Solution Doc`, creates a Start
Menu shortcut, optionally creates a desktop shortcut, and leaves per-user settings,
credentials, projects, and generated documents untouched during upgrade or uninstall.
