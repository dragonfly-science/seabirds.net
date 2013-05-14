# Need a general way to specify what virtualenv to use
#. ~/.virtualenvs/seabirds/bin/activate
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd DIR
echo "Using virtualenv $VIRTUAL_ENV"
cd seabirds && ./manage.py test cms profile comments $@
