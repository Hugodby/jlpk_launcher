#!/usr/bin/python2
from launcher import Launcher

local_tmp_folder = '/opt/joulupukki/scripts/tmp/packages_folder_nightly_windows/'
local_ddl_folder = '/opt/joulupukki/scripts/repos/windows/'

launcher = Launcher(
    'example-windows', 
    'https://some.depot.com/example-windows', 
    'windows', 
    'http://buildmachine-01.joulupukkidomain.com/v3/users/someone/',
    local_tmp_folder,
    local_ddl_folder,
)


build_id = launcher.launch_build()
if launcher.wait_build(build_id):
    archive = launcher.download_build(build_id)
    launcher.extract_build(archive)
    launcher.move_package('win32/example-windows-nightly.exe')
    print("Build succeeded !")
    
    # After build command
    launcher.after_build_cmds([
        "rsync -arv --delete "+local_ddl_folder+" someone@ftp.server.com:/var/www/example/windows"
    ])
else:
    print("Build timed-out or failed.")
