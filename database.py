import sqlalchemy as db
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from datetime import datetime

class Base(DeclarativeBase):
    pass 

# Vehicle model 
class VehicleRecord(Base):
    __tablename__ = "vehicle_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    count: Mapped[int]
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)

# create SQLite database
DATABASE_URL = "sqlite:///traffic_monitor.db"
engine = db.create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)