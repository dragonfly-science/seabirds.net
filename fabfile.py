import os
from fabric.api import sudo, cd, local, env, run, prefix 
from contextlib import contextmanager as _contextmanager


#### Begin env settings ####
env.hosts = ['localhost']
env.production_server = 'www.dragonfly.co.nz'

def prod():
   """ Use production server settings """
   env.hosts = [env.production_server]

env.user = os.environ['USER']
env.path = '~/dragonfly/dragonflyweb'
env.project = 'dragonflyweb'
env.db = 'dragonflyweb'
env.repo = 'gitosis@code.dragonfly.co.nz:dragonflyweb.git'
env.activate = 'source /usr/local/bin/virtualenvwrapper.sh; workon %(project)s' % env
env.sitename = 'www'
#### End env settings ####

#### Private functions ####
@_contextmanager
def _virtualenv():
    with cd(env.path):
        with prefix(env.activate):
            yield

def _patches_migrate():
    """ A simple database migration schema.

    The database has a table 'patches' that contains the name of each patch that has been run.
    Any sql file in the directory (sitename)/patches is found.
    Each file is run, unless it is already listed in the database.
    If it is run successfully, a corresponding entry is put in the database """

def _patches_markall():
    """ Update the database so that all patches are marked as having been run """

#### End private functions ####

def install_tools():
    "Make sure that the system has required tools"
    sudo("aptitude install python-setuptools")
    sudo("easy_install pip")
    sudo("pip install virtualenvwrapper")
    with cd("%(path)s" % env):
        run('source /usr/local/bin/virtualenvwrapper.sh; mkvirtualenv --no-site-packages %(project)s' % env)
    sudo("pip install ssh==dev") # Get the latest versions
    sudo("pip install fabric==dev") # Get the latest versions

def install_code():
    "Clone the git repository"
    run('mkdir -p %(path)s' % env)
    with cd("%(path)s" % env):
        run('git clone %(repo)s %(path)s' % env)

def install_requirements():
    "Install any required python packages from the requirements.txt file"
    with _virtualenv():
        run('pip install -r requirements.txt')


def install_apache():
    run('mkdir -p /usr/local/django')
    sudo('ln -s %(path)s/%(sitename)s /usr/local/django/%(sitename)s.%(project)s' % env)  

def initialize():
    "Run this on a new host to get the project set up"
    install_tools()
    install_code()
    install_requirements()

def git_pullpush():
    "Make sure that any commits are synchronised with the server"
    with cd("%(path)s" % env):
        run('git pull')
        run('git push')

def get_live_media():
    "Copy media from the production server to the local machine"
    local('sudo rsync -avzL %(user)s@%(production_server)s:/var/www/dragonfly/media/ /usr/local/django/www/media --exclude=*.css --exclude=*.js' % env)
    local('sudo chown %(user)s:dragonfly /usr/local/django/www/media -R' % env)

def get_live_database():
    "Copy live database from the production server to the local machine"
    local('dropdb %(db)s' % env)
    local('ssh %(production_server)s pg_dump -U %(db)s -C %(db)s | psql postgres' % env)

def get_uptodate():
    with cd("%(path)s" % env):
        run('git pull')
    get_live_media()
    get_live_database()

def validate():
    "Run django validation"
    with _virtualenv():
        with cd('%(sitename)s'% env):
            run('python manage.py validate')
