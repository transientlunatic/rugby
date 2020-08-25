from flask_api import FlaskAPI
app = FlaskAPI(__name__)
from rugby.models import *
if 'RUGBYDB' in os.environ:
    db = os.environ['RUGBYDB']
else:
    db = f"{rugby.__path__[0]}/rugby.db"
engine = create_engine(f'sqlite:///{db}')


# Adding the new conference map
try:
    ConferenceMap.__table__.create(bind = engine)
except sqlalchemy.exc.OperationalError:
    pass
