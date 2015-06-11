from __future__ import print_function
import json, time, urllib, urllib2, os, shutil, tarfile, glob, subprocess

class Launcher(object):
    def __init__(self, package_name, source_url, plateform, api_url, tmp_folder, ddl_folder): 
        self.package_name = package_name
        self.source_url = source_url
        self.plateform = plateform
        self.api_url = api_url + package_name
        self.tmp_folder = tmp_folder
        self.ddl_folder = ddl_folder

    def launch_build(self, source_type='git', branch='packaging', snapshot=True):
        build_param = json.dumps({
            'source_url': self.source_url, 
            'source_type': source_type, 
            'branch': branch, 
            'snapshot': snapshot
        })
        request = urllib2.Request(self.api_url+'/build')
        request.add_header('Content-Type', 'application/json')
        build_id = urllib2.urlopen(request, build_param)
        print("Build", str(build_id), "launched for package", self.package_name, ".")
        return build_id

    def wait_build(self, build_id, timeout=7200, waiting_step=300):
        start_date = time.time() 
        limit_date = start_date + timeout 
        build_finished = False
        print("Waiting for build", str(build_id), "of package", self.package_name, ".")
        while time.time() < limit_date and not build_finished:
            time.sleep(waiting_step)
            status = self.get_api('/builds/'+str(build_id), 'status')
            print("    Build", str(build_id), "of package", self.package_name, "status :", status)
            if status == 'succeeded':
                build_finished = True
        return build_finished

    def download_build(self, build_id):
        directory = os.path.join(self.tmp_folder, 'downloads')
        shutil.rmtree(directory, ignore_errors=True)
        os.makedirs(directory)
        archive_url = self.api_url + '/builds/'+str(build_id)+'/download/archive'
        print("Downloading", archive_url, "...") 
        response = urllib2.urlopen(archive_url).read()
        archive = os.path.join(directory, 'ring-client-'+self.plateform+'.tar.gz')
        dlfile = open(archive, 'wb')
        dlfile.write(response)
        dlfile.close()
        return archive

    def extract_build(self, archive):
        directory = os.path.join(self.tmp_folder, 'packages')
        shutil.rmtree(directory, ignore_errors=True)
        print("Extracting", archive, "to", directory, "...")
        os.makedirs(directory)
        tar = tarfile.open(archive, 'r:gz')
        tar.extractall(directory)
        tar.close()

    def move_package(self, package_file):
        src_file = os.path.join(self.tmp_folder, 'packages', package_file)
        dest = os.path.join(self.ddl_folder)
        if not os.path.exists(dest):
            os.makedirs(dest)
        package_ext = os.path.splitext(package_file)[1]
        file_name = 'ring-' + time.strftime('%Y%m%d%H%M') + package_ext
        dest_file = os.path.join(dest, file_name) 
        print("Moving file", src_file, "to", dest_file)
        os.rename(src_file, dest_file)
        link_file = os.path.join(dest, 'ring-nightly' + package_ext)
        if os.path.lexists(link_file):
            os.remove(link_file)
        os.symlink(file_name, link_file)

    def get_api(self, url, var):
        response = json.loads(urllib2.urlopen(self.api_url+url).read())
        return response.get(var)

    def after_build_cmds(self, cmds):
        for cmd in cmds:
            print("Running :", cmd)
            process = subprocess.Popen(
                cmd+' 2>&1',
                stdout=subprocess.PIPE,
                shell=True
            )
            stdout,_ = process.communicate()
            print(stdout)

