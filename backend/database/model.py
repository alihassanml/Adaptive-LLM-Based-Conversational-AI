from sqlalchemy import Boolean,Integer,Column,String,ForeignKey,Float,DateTime, Enum, Text,LargeBinary
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database.database import Base

class Sginup(Base):
    __tablename__ = 'Sginup'
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String)    
    username = Column(String,unique=True,index=True)
    email = Column(String,unique=True,index=True)
    password = Column(String,index=True)