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
env.remote_dir = '/home/seabirds/seabirds.net'
env.local_dir = os.getcwd()

#### Private functions ####
@_contextmanager
def _virtualenv():
    """
    Wrap functions in the virtualenv.

    NOTE: this may not work at all if the virtualenv is already activated,
    and won't work if the virtualenvwrapper.sh script is installed in the user's
    .local dir.

    TODO: It is often suggested to directly source the venv activation script:

    http://stackoverflow.com/questions/1180411/activate-a-virtualenv-via-fabric-as-deploy-user
    """
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
    # TODO: Should we really overwrite sitesettings.py?
    # This would blast away information that a developer may have
    # customised.
    get('%(remote_dir)s/seabirds/sitesettings.py' % env, local_path='seabirds')
    get('%(remote_dir)s/seabirds/secrets.py' % env, local_path='seabirds')

def get_live_media():
    "Copy media from the production server to the local machine"
    local('rsync -avz -e "ssh -l seabirds" seabirds@%(production_server)s:%(remote_dir)s/seabirds/media %(local_dir)s/seabirds/ --exclude=*.css --exclude=*.js' % env)
    local('rsync -avzL -e "ssh -l seabirds" seabirds@%(production_server)s:%(remote_dir)s/static %(local_dir)s/ --exclude=*.css --exclude=*.js' % env)
    local('chown %(local_user)s:dragonfly %(local_dir)s -R' % env)

def get_live_database():
    "Copy live database from the production server to the local machine"
    with cd('%(remote_dir)s' % env):
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
    with cd("%(remote_dir)s" % env):
        run('git pull')

def put_secrets():
    "Put files that aren't in the checkout, such as sitesettings.py"
    put('sitesettings.py', remote_path='%(remote_dir)s/seabirds' % env)
    put('seabirds/secrets.py', remote_path='%(remote_dir)s/seabirds' % env)

def install():
    "Fetch any new software that is required and run syncdb"
    with cd('%(remote_dir)s' % env):
        run('pip install -r requirements.txt')

def update():
    with cd('%(remote_dir)s' % env):
        run('pip install -r requirements.txt')
    with cd('%(remote_dir)s/seabirds' % env):
        run('python manage.py cuckoo run')

def cuckoo():
    with cd('%(remote_dir)s/seabirds' % env):
        run('python manage.py cuckoo run')

def syncdb():
    with cd('%(remote_dir)s/seabirds' % env):
        run('python manage.py syncdb')

def validate():
    "Run django validation"
    with cd('%(remote_dir)s/seabirds' % env):
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
