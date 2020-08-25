from rugby.models import *
if 'RUGBYDB' in os.environ:
    db = os.environ['RUGBYDB']
    app.config['JWT_SECRET_KEY'] = os.environ['RUGBY_SECRET']
else:
    db = f"{rugby.__path__[0]}/rugby.db"
    app.config['JWT_SECRET_KEY'] = 'test'
engine = create_engine(f'sqlite:///{db}')
ConferenceMap.__table__.create(bind = engine)
