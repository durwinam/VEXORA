from sqlalchemy import create_engine, String, Integer, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from datetime import datetime, timezone
from app.core import settings
from pathlib import Path
Path('data').mkdir(exist_ok=True)
engine=create_engine(settings.database_url, connect_args={'check_same_thread':False} if settings.database_url.startswith('sqlite') else {})
SessionLocal=sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Base(DeclarativeBase): pass
class Admin(Base):
    __tablename__='admins'; id:Mapped[int]=mapped_column(primary_key=True); username:Mapped[str]=mapped_column(String(64),unique=True); password_hash:Mapped[str]=mapped_column(String(512)); role:Mapped[str]=mapped_column(String(32),default='operator'); path:Mapped[str]=mapped_column(String(128),unique=True); active:Mapped[bool]=mapped_column(Boolean,default=True); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Panel(Base):
    __tablename__='panels'; id:Mapped[int]=mapped_column(primary_key=True); owner_id:Mapped[int]=mapped_column(ForeignKey('admins.id')); name:Mapped[str]=mapped_column(String(100)); kind:Mapped[str]=mapped_column(String(32)); base_url:Mapped[str]=mapped_column(String(500)); credential_blob:Mapped[str]=mapped_column(Text); active:Mapped[bool]=mapped_column(Boolean,default=True)
class Product(Base):
    __tablename__='products'; id:Mapped[int]=mapped_column(primary_key=True); owner_id:Mapped[int]=mapped_column(ForeignKey('admins.id')); name:Mapped[str]=mapped_column(String(120)); panel_id:Mapped[int]=mapped_column(ForeignKey('panels.id')); traffic_bytes:Mapped[int]=mapped_column(Integer,default=0); duration_days:Mapped[int]=mapped_column(Integer,default=30); price:Mapped[int]=mapped_column(Integer,default=0); active:Mapped[bool]=mapped_column(Boolean,default=True)
class Order(Base):
    __tablename__='orders'; id:Mapped[int]=mapped_column(primary_key=True); owner_id:Mapped[int]=mapped_column(ForeignKey('admins.id')); product_id:Mapped[int]=mapped_column(ForeignKey('products.id')); username:Mapped[str]=mapped_column(String(100)); status:Mapped[str]=mapped_column(String(32),default='pending'); config:Mapped[str]=mapped_column(Text,default=''); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Receipt(Base):
    __tablename__='receipts'; id:Mapped[int]=mapped_column(primary_key=True); owner_id:Mapped[int]=mapped_column(ForeignKey('admins.id')); order_id:Mapped[int]=mapped_column(ForeignKey('orders.id')); file_path:Mapped[str]=mapped_column(String(500)); status:Mapped[str]=mapped_column(String(32),default='pending'); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))
class Audit(Base):
    __tablename__='audit'; id:Mapped[int]=mapped_column(primary_key=True); actor:Mapped[str]=mapped_column(String(100)); action:Mapped[str]=mapped_column(String(100)); ip:Mapped[str]=mapped_column(String(64)); detail:Mapped[str]=mapped_column(Text,default=''); created_at:Mapped[datetime]=mapped_column(DateTime,default=lambda:datetime.now(timezone.utc))

def init_db(): Base.metadata.create_all(engine)
