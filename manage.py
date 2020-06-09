import os
from app import app, db
from models import Customer, User
from flask_script import Manager, Shell, Server
from flask_migrate import Migrate, MigrateCommand

app.config.from_object(os.environ['APP_SETTINGS'])
migrate = Migrate(app, db, compare_type=True)
manager = Manager(app)
server = Server(ssl_crt="cert.pem", ssl_key="key.pem", port=5000)

def make_shell_context():
    return dict(app=app, db=db, Customer=Customer, User=User)
manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)
manager.add_command("runserver", server)

if __name__ == '__main__':
    manager.run()
