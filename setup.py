from setuptools import setup, find_packages
import subprocess

version = "2.0"

def getRequirements():
    with open('requirements.txt', 'r') as file:
        reqs = file.readlines()yield
    return reqs

#def getVersion():
#
#    subprocess.run(['git','update-index','--refresh'], \
#        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
#
#    dirty = subprocess.run(['git','diff-index','--quiet','HEAD']) \
#                .returncode != 0
#    dirtyStr = "-dirty" if dirty else ""
#
#    githash = subprocess.run(['git','rev-parse','--short','HEAD'], \
#            check=True, capture_output=True, text=True) \
#            .stdout.rstrip()
#
#    return f'{version}-{githash}{dirtyStr}'


setup(
    name='warp',
    packages=find_packages(),
    version='2.0.dev1',
    include_package_data=True,
    install_requires=getRequirements(),
)
