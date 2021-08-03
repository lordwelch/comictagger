# Script to be run inside appveyor for a full build
python -m venv venv
./venv/Scripts/Activate.ps1
#pip install wheel
pip install -r requirements-dev.txt
pip install -r requirements.txt
python ./setup.py --version
pyinstaller.exe -y --name="comictagger" --add-data 'comictaggerlib/ui/*.ui;ui' --add-data 'comictaggerlib/graphics;graphics' -i windows/app.ico --version-file file_version_info.py comictagger.py
pyinstaller.exe -F --name="comictagger" --add-data 'comictaggerlib/ui/*.ui;ui' --add-data 'comictaggerlib/graphics;graphics' -i windows/app.ico --version-file file_version_info.py comictagger.py

mv -Force dist/comictagger.exe "comictagger-$([System.Diagnostics.FileVersionInfo]::GetVersionInfo("$pwd/dist/comictagger.exe").FileVersion).exe"

rm -Force -ErrorAction SilentlyContinue "./comictagger-$([System.Diagnostics.FileVersionInfo]::GetVersionInfo("$pwd/dist/comictagger/comictagger.exe").FileVersion).zip"
Compress-Archive -Path dist/comictagger -DestinationPath "./comictagger-$([System.Diagnostics.FileVersionInfo]::GetVersionInfo("$pwd/dist/comictagger/comictagger.exe").FileVersion).zip"

deactivate
