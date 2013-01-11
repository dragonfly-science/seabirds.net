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
env.remote_dir = '/home/seabirds/webapps/seabirds_live/seabirds.net/'
env.local_dir = os.path.dirname(__file__)

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
def get_secrets():
    "Get files that aren't in the checkout, such as sitesettings.py"
    with lcd(env.local_dir):
        # We get a copy of the production sitesettings.py, but we don't use it for local
        # development (hence it's not kept in seabirds/).
        get('%(remote_dir)s/seabirds/sitesettings.py' % env, local_path='sitesettings_production.py')
        get('%(remote_dir)s/seabirds/secrets.py' % env, local_path='seabirds/')

def get_live_media():
    "Copy media from the production server to the local machine"
    local('rsync -avz -e "ssh -l seabirds" seabirds@%(production_server)s:%(remote_dir)s/seabirds/media %(local_dir)s/seabirds/ --exclude=*.css --exclude=*.js' % env)
    local('rsync -avzL -e "ssh -l seabirds" seabirds@%(production_server)s:%(remote_dir)s/static %(local_dir)s/ --exclude=*.css --exclude=*.js' % env)
    local('chown %(local_user)s:dragonfly %(local_dir)s -R' % env)

def get_live_database():
    "Copy live database from the production server to the local machine"
    with cd(env.remote_dir), lcd(env.local_dir):
        run('pg_dump -U seabirds -C seabirds > dumps/latest.sql')
        get('dumps/latest.sql', local_path='dumps')
        run('rm dumps/latest.sql')
        with settings(warn_only=True):
            local('dropdb seabirds')
        local('psql postgres -f dumps/latest.sql')
        # Change the site object to use localhost:8000
        local("""echo "update django_site set domain = 'localhost:8000', name = 'Seabirds.net (local)' where domain='seabirds.net'" | psql -d seabirds""")

def runserver():
    with lcd('seabirds'), _virtualenv(), settings(warn_only=True):
        local('python manage.py runserver')

def pull():
    local('git pull')
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
    put('sitesettings_production.py', remote_path='%(remote_dir)s/seabirds/sitesettings.py' % env)
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

def test():
    with cd('%(remote_dir)s/seabirds' % env):
        run('python manage.py test cms')
        run('python manage.py test profile')

def restart():
    "Restart the server"
    run('/home/seabirds/webapps/django/apache2/bin/restart')

def push():
    git_push()
    put_secrets()
    update()
    validate()
    restart()

def _environment_settings(environment):
    app_dir = '/home/seabirds/webapps/'
    production_dir = app_dir + 'seabirds_live/seabirds.net'

    # Deploy to production or staging?
    production = False
    if environment == 'production':
        production = True

    if production:
        remote_dir = production_dir
        settings_file = 'sitesettings_production.py'
        venv = 'seabirds_live'
    else:
        remote_dir = app_dir + 'seabirds_dev/seabirds.net'
        settings_file = 'sitesettings_dev.py'
        venv = 'seabirds_dev'

    return production, settings_file, venv, remote_dir, production_dir


def deploy(environment='staging', specific_commit=None):
    """ Deploy to server

    By default we deploy to staging. If environment is set to 'production', then we'll
    deploy to production.

    Deploy will sync from the master branch of the seabirds.net git repo, so
    make sure your local changes are pushed if you want to see them on the site.
    """
    is_production, settings_file, venv, env.remote_dir, production_dir = _environment_settings(environment)
    
    # apache stop
    # TODO: Ideally this should put up a "maintenance mode" static html page
    run('%(remote_dir)s/../apache2/bin/stop' % env)

    if not is_production:
        # Whenever we deploy to the dev server, we take a snapshot of
        # the production database and media/static content
        with cd('%(remote_dir)s/..' % env):
            # Expects password credentials to be in ~/.pgpass
            run('pg_dump -U seabirds -c seabirds > seabirds.sql')
            # Horrible hack to clear the dev database of all data, since we
            # can't programmatically create/drop dbs within webfaction
            run("""psql -U seabirds_dev -d seabirds_dev -qAtX -c "select 'TRUNCATE table ' || quote_ident(table_schema) || '.' || quote_ident(table_name) || ' CASCADE;' from information_schema.tables where table_type = 'BASE TABLE' and not table_schema ~ '^(information_schema|pg_.*)$'" | psql -U seabirds_dev -d seabirds_dev -qAtX""")
            run('psql -U seabirds_dev -d seabirds_dev -f seabirds.sql')
            # clean up
            run('rm seabirds.sql')
            # Change the site object to use dev.seabirds.net
            run("""echo "update django_site set domain = 'dev.seabirds.net', name = 'Seabirds.net (dev)' where domain='seabirds.net'" | psql -U seabirds_dev -d seabirds_dev""")
        with cd(env.remote_dir):
            run('rsync -avz %s/seabirds/media %s/seabirds/. --exclude=*.css --exclude=*.js' % (
                production_dir, env.remote_dir))
            # This dir can probably be ignored since it is created by collecstatic (or at least it should be)
            run('rsync -avz %s/static %s/. --exclude=*.css --exclude=*.js' % (
                production_dir, env.remote_dir))
    
    with cd(env.remote_dir):
        # Fetch latest code and then upload our local copies of sitesettings and secrets
        run('git pull')
        if specific_commit:
            # If we want to deploy a specific commit, reset to it
            run('git reset --hard %s' % specific_commit)
            run('git clean -f -d')
        with prefix('source /home/seabirds/.virtualenvs/%s/bin/activate' % venv):
            run('pip install -r requirements.txt')
        with lcd(env.local_dir):
            put(settings_file, remote_path='%(remote_dir)s/seabirds/sitesettings.py' % env)
            put('seabirds/secrets.py', remote_path='%(remote_dir)s/seabirds' % env)
            run('make clean') # remove pyc and pyo

    with cd('%(remote_dir)s/seabirds' % env):
        # Run migrations, syncdb and our test suite
        with prefix('source /home/seabirds/.virtualenvs/%s/bin/activate' % venv):
            run('python manage.py cuckoo run')
            run('python manage.py syncdb')
            run('python manage.py validate')
            run('python manage.py collectstatic --noinput')
            run('cd .. && make test')

    from fabric.contrib.files import upload_template

    # Unless this is production, print out the sys.path in wsgi.py after setting 
    # up virtualenv
    debug_print = 'print sys.path'
    if is_production:
        debug_print = ''
    upload_template('%(local_dir)s/wsgi.py.TEMPLATE' % env, '%(remote_dir)s/wsgi.py' % env,
            context={'venv':venv, 'webapp':venv, 'debug_print': debug_print})

    # restart apache
    run('%(remote_dir)s/../apache2/bin/start' % env)

def fetch_results(environment='staging', specific_commit=None):
    """ Just fetch the test results from the remote server.  """
    _, _, _, env.remote_dir, _ = _environment_settings(environment)

    with cd('%(remote_dir)s/seabirds' % env):
        get('nosetests.xml', '%(local_dir)s/seabirds/.' % env)
        get('coverage.xml', '%(local_dir)s/seabirds/.' % env)
        get('htmlcov', '%(local_dir)s/seabirds/.' % env)

