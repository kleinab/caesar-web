from fabric.api import *

env.project_name = 'caesar'
env.project_path = '/var/django/caesar'

env.roledefs = {
    'prod': ['caesar.xvm.mit.edu'],
}

env.roles = ['prod']

def deploy():
    """
    Pulls the latest code from git and deploys it.
    """
    update_code()
    install_project()
    restart_webserver()

def update_code():
    with cd(env.project_path):
        run('git pull')

def install_project():
    # symlink the caesar apache configuration file to apache
    sudo('cd /etc/apache2/sites-enabled; ln -sf %(project_path)s/apache/%(project_name)s %(project_name)s' % env)
    with cd(env.project_path):
        run('python manage.py collectstatic --noinput')
        run('python manage.py syncdb --noinput')
        run('python manage.py migrate')

def restart_webserver():
    sudo('service apache2 restart')

