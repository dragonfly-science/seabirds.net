import os
from fabric.api import sudo, cd, local, env, run, lcd, get, settings, put, prefix
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

#### Private functions ####
@_contextmanager
def _virtualenv():
    local('/bin/bash /usr/local/bin/virtualenvwrapper.sh; workon seabirds')
    yield
    local('deactivate')
#### End private functions ####


# Commands for  getting data from the server
def git_pull():
    "Make sure that any commits are synchronised with the server"
    local('git pull')

def get_secrets():
    "Get files that aren't in the checkout, such as sitesettings.py"
    get('%(path)s/seabirds/sitesettings.py' % env, local_path='.')
    get('%(path)s/seabirds/secrets.py' % env, local_path='seabirds')

def get_live_media():
    "Copy media from the production server to the local machine"
    local('rsync -avz -e "ssh -l seabirds" seabirds@%(production_server)s:%(path)s/seabirds/media %(local_path)s/seabirds/ --exclude=*.css --exclude=*.js' % env)
    local('rsync -avzL -e "ssh -l seabirds" seabirds@%(production_server)s:%(path)s/static %(local_path)s/ --exclude=*.css --exclude=*.js' % env)
    local('chown %(local_user)s:dragonfly %(local_path)s -R' % env)

def get_live_database():
    "Copy live database from the production server to the local machine"
    with cd('%(path)s' % env):
        run('pg_dump -U seabirds -C seabirds > dumps/latest.sql')
        get('dumps/latest.sql', local_path='dumps')
        with settings(warn_only=True):
            local('dropdb seabirds')
        local('psql postgres -f dumps/latest.sql')

def runserver():
    with lcd('seabirds'):
        with _virtualenv():
            with settings(warn_only=True):
                local('python manage.py runserver')

def pull():
    git_pull()
    get_secrets()
    get_live_media()
    get_live_database()


# Commands for deploying to the remote server
def git_push():
    "Make sure that any commits are synchronised with the server"
    local("git push")
    with cd("%(path)s" % env):
        run('git pull')

def put_secrets():
    "Put files that aren't in the checkout, such as sitesettings.py"
    put('sitesettings.py', remote_path='%(path)s/seabirds' % env)
    put('seabirds/secrets.py', remote_path='%(path)s/seabirds' % env)

def install():
    "Fetch any new software that is required and run syncdb"
    with cd('%(path)s' % env):
        run('pip install -r requirements.txt')

def update():
    with cd('%(path)s' % env):
        run('pip install -r requirements.txt')
    with cd('%(path)s/seabirds' % env):
        run('python manage.py cuckoo run')

def syncdb():
    with cd('%(path)s/seabirds' % env):
        run('python manage.py syncdb')

def validate():
    "Run django validation"
    with cd('%(path)s/seabirds' % env):
        run('python manage.py validate')

def restart():
    "Restart the server"
    run('/home/seabirds/webapps/django/apache2/bin/restart')

def push():
    git_push()
    put_secrets()
    update()
    validate()
    restart()


