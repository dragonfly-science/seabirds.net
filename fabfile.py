import os
from fabric.api import sudo, cd, local, env, run, lcd, get, settings
from contextlib import contextmanager as _contextmanager


#### Begin env settings ####

env.user = 'seabirds'
env.repo = 'git@github.com:dragonfly-science'
env.sitename = 'seabirds'
env.production_server = 'seabirds.webfactional.com'
env.local_user = os.environ['USER']

env.hosts = [env.production_server]
env.path = '/home/seabirds/seabirds.net'
env.local_path = os.getcwd()
env.activate = 'source /usr/local/bin/virtualenvwrapper.sh; workon seabirds' % env
#### End env settings ####

#### Private functions ####
#@_contextmanager
#def _virtualenv():
#    with prefix(env.activate):
#        yield
#### End private functions ####


def git_pull():
    "Make sure that any commits are synchronised with the server"
    with cd("%(path)s" % env):
        run('git pull')

def get_live_media():
    "Copy media from the production server to the local machine"
    local('rsync -avz -e "ssh -l seabirds" seabirds@%(production_server)s:%(path)s/seabirds/media %(local_path)s/seabirds/ --exclude=*.css --exclude=*.js' % env)
    local('rsync -avzL -e "ssh -l seabirds" seabirds@%(production_server)s:%(path)s/static %(local_path)s/ --exclude=*.css --exclude=*.js' % env)
    local('chown %(local_user)s:dragonfly %(local_path)s -R' % env)

def get_live_database():
    "Copy live database from the production server to the local machine"
    with cd('%(path)s' % env):
        run('pg_dump -U seabirds -C seabirds > dumps/latest.sql')
        get('seabirds/dumps/latest.sql', local_path='dumps')
        with settings(warn_only=True):
            local('dropdb seabirds')
        local('psql postgres -f dumps/latest.sql')

def local_uptodate():
    local('git pull')
    get_live_media()
    get_live_database()

def validate():
    "Run django validation"
    with cd('%(path)s/seabirds' % env):
        run('python manage.py validate')
