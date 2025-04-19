from sqlalchemy import create_engine

from core.config import settings
from models import Base

engine = create_engine(settings.database_url)

# Create the tables
Base.metadata.create_all(bind=engine)