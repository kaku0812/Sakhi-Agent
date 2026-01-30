from sqlalchemy import Table, Column, Integer, Float, Boolean, DateTime
from sqlalchemy import MetaData
from datetime import datetime

metadata = MetaData()

snapshots = Table(
    "snapshots",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("local_id", Integer, nullable=False),
    Column("timestamp", DateTime, nullable=False, default=datetime.utcnow),
    Column("battery", Integer, nullable=False),
    Column("network", Boolean, nullable=False),
    Column("lat", Float, nullable=False),
    Column("lng", Float, nullable=False)
)
