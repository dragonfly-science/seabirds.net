This repo is the code for [Seabirds.net](http://seabirds.net) 
is the website of the World Seabird Union, an umbrella organisation focused on seabird research. 

It is a fairly standard Django application. Feel free to contribute by forking
the code and commenting on issues.

## Setup

```
sudo apt-get install libpg-dev postgresql
mkvirtualenv seabirds
pip install -r requirements.txt
sudo su postgres
psql template1
```

At the `template1=#` prompt:
```
CREATE USER [your username] CREATEDB;
CREATE USER seabirds;
```

Why?
* The user you develop under needs to be able to create databases.
* The seabirds user has a number of permissions assigned to it when loading
  a database dump from the production server.

Now copy `local_settings.py.TEMPLATE` to `local_settings.py` and edit it
to configure to match your local db:
```
cp local_settings.py.TEMPLATE local_settings.py
vim local_settings.py
```

Go back to your login, and then ensure your public ssh key is in the
authorised_keys of the server you are deploying to.

```
fab get_live_database # Download live db and load it locally
fab get_live_media    # Download all the media assets
fab get_secrets       # Get API keys etc and example sitesettings.py
```

