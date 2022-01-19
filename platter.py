import jenkins
import sys
import inspect
import os
from xml.etree import ElementTree as et

#Initial Configuration
server = jenkins.Jenkins("{}".format(os.environ.get('JENKINS_URL')), username="{}".format(os.environ.get('USERNAME')),password=os.environ.get('JENKINS_API_KEY'))

#Check if you need any sanity check by printing the user or version from below
#user = server.get_whoami()
#version = server.get_version()
def help():
    print("""
    Platter CLI v1

    Platter is a Python3 Tool to Support Jenkins.
    Intended to speed up any changing configuration with a fraction of the clicking.
    Current methods supported: listing jobs, and returning/replacing the SCM branch configuration.

    CLI Documentation:
        platter help

    Available Commands:
        list-jobs path                      : Shows jobs that are in a specific path. To see root folder pass in  /
        get-branch job_path                 : Returns Remote Source Control Management Branch
        replace-branch job_path new_branch  : Updates the job's config.xml with the new branch. Automatically adds */


    Examples:
        list-jobs foo
        list-jobs /
        get-branch foo/bar
        replace-branch foo/bar master

    """)

def list_jobs(path: str):
    """
    path: If "root", no recursive depth. Otherwise show all jobs that match the path name, regardless of env.
    """
    if path == '/':
        depth = 0
    else:
        depth = 5 #assuming no job_path is nested under 5 paths
    jobs = server.get_jobs(folder_depth = depth)
    for i in jobs:
        #Finding paths
        if path in i['fullname'] or depth == 0:
            if i['_class'] == "com.cloudbees.hudson.plugins.folder.Folder":
                print("folder:  ",i['fullname'])
            #Found folder we want to list
            else:
                print("job_path:", i['fullname'])

def get_branch(job_path: str) -> str:
    """
    job_path: Path to a current jenkins job_path, i.e 'foo/bar'
    """
    tmp = et.fromstring(server.get_job_config(job_path))
    branch = tmp.find('definition/scm/branches/hudson.plugins.git.BranchSpec/name').text
    print(branch)
    return branch

def replace_branch(job_path: str, new_branch: str):
    """
    job_path: Path to a current jenkins job_path, i.e 'foo/bar'
    new_branch: (Automatically adds the */ prefix). Replaces the branch in the jenkins config file with a new branch.
    """
    config = server.get_job_config(job_path)
    oldBranchName = get_branch(job_path)
    old_section ="{}".format(oldBranchName)
    new_section = "*/{}".format(new_branch)
    new_config = config.replace(old_section,new_section)
    print("Updating {}'s branch from {} to */{}".format(job_path,oldBranchName,new_branch))
    server.reconfig_job(job_path, new_config)


if __name__ == '__main__':
    if len(sys.argv) == 1: #Assuming they just ran the command and passed in nothing
        help()
    else:
        args = inspect.getfullargspec(globals()[sys.argv[1].replace('-','_')])
        possibleParameters = len(args[0])+2
        params=sys.argv[2:possibleParameters]
        globals()[sys.argv[1].replace('-','_')](*params)
