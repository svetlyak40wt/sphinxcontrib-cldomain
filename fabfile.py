from fabric.api import local, lcd, abort, run, settings, env
from fabric.contrib.project import rsync_project
from fabric.decorators import task
from os.path import expandvars
import os

env.use_ssh_config = True


def clean():
    with lcd("doc"):
        local("rm -rf html/")


@task
def build():
    """build the documentation"""
    clean()
    with lcd("doc"):
        local("sphinx-build -b html -E . html")


@task
def pypi_upload():
    """upload a new version to pypi"""
    local("python setup.py egg_info --tag-build= --no-date sdist upload")


def inc_version():
    version = float(local("git describe --tags --abbrev=0", capture=True))
    version += 0.1
    return version


@task
def release_minor():
    generate_version(inc_version())


@task
def release_major():
    generate_version(float(int(inc_version() + 1.0)))


def generate_version(version):
    filename = "sphinxcontrib/version.lisp-expr"
    with open(filename, "w") as version_file:
        version_file.write('"' + str(version) + '"')
    local("cat " + filename)
    local("git add " + filename)
    message = "Released " + str(version)
    local("git commit -m '%s'" % message)
    local("git tag -m '" + message + "' %s" % version)


try:
    execfile(expandvars("$HOME/.projects.py"))

    @task
    def deploy():
        """deploy a prod version"""
        env = os.environ
        env["GOOGLE_ANALYTICS"] = "true"
        build()
        project_env = PROJECTS["sphinxcontrib-cldomain"]
        env.hosts = [project_env["host"]]
        assert project_env["remote_dir"]
        with settings(host_string=project_env["host"]):
            rsync_project(project_env["remote_dir"], "doc/html/")

except:
    pass
