# Windows packaging

Run on Windows with Python 3.12 using scripts\\setup_dev.bat and scripts\\package_release.bat.

The production runtime is a PyInstaller one-folder build. Vegas_Total_Solution_Doc.spec
keeps the Qt Core/Gui/Widgets stack, HTTP support, image formats, PyMuPDF binaries,
python-docx, requests, and Windows keyring support. It excludes only confirmed-unused
optional Qt modules and development/test packages. UPX remains disabled because Qt DLL
compression can cause startup and antivirus issues.

The installer uses Inno Setup 6 with Compression=lzma2/ultra64,
SolidCompression=yes, and LZMAUseSeparateProcess=yes.

GitHub Actions performs a broad baseline build and the optimized spec build, writes
artifacts/package_size_before.txt and artifacts/package_size_after.txt, prints the
installer reduction and ten largest files, warns above 120 MB, and fails above 160 MB.
The exact measurements are uploaded in the package-size-report artifact. No package
size is estimated or reported before that Windows run completes.

The release artifact is dist/installer/Vegas_Total_Solution_Doc_Setup.exe.
