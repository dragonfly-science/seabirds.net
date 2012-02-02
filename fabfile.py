import os
from fabric.api import sudo, cd, local, env, run, prefix 
from contextlib import contextmanager as _contextmanager


#### Begin env settings ####

env.project = 'seabirds.net'
env.user = os.environ['USER']
env.repo = 'git@github.com:dragonfly-science'
env.sitename = 'seabirds'
env.production_server = 'seabirds.webfactional.com'
env.db='seabirds'

def dev():
    env.hosts = ['localhost']
    env.path = '/home/edward/dragonfly/seabirds.net'
    env.activate = 'source /usr/local/bin/virtualenvwrapper.sh; workon %(project)s' % env

def prod():
    """ Use production server settings """
    env.hosts = [env.production_server]
    env.path = '/home/seabirds/seabirds.net'
    env.activate = ''
#### End env settings ####

#### Private functions ####
@_contextmanager
def _virtualenv():
    with cd(env.path):
        with prefix(env.activate):
            yield

#### End private functions ####


def git_pull():
    "Make sure that any commits are synchronised with the server"
    with cd("%(path)s" % env):
        run('git pull')

def get_live_media():
    "Copy media from the production server to the local machine"
    local('sudo rsync -avzL seabirds@%(production_server)s:/home/seabirds/seabirds.net/seabirds/media /usr/local/django/seabirds.net --exclude=*.css --exclude=*.js' % env)
    local('sudo chown %(user)s:dragonfly /usr/local/django/seabirds.net/media -R' % env)

def get_live_database():
    "Copy live database from the production server to the local machine"
    local('dropdb %(db)s' % env)
    local('ssh seabirds@%(production_server)s pg_dump -U %(db)s -C %(db)s | psql postgres' % env)

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
