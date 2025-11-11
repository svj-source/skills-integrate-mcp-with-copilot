from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    schedule = Column(String(200))
    max_participants = Column(Integer, default=0)

    enrollments = relationship("Enrollment", back_populates="activity", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    email = Column(String(200), primary_key=True, index=True)
    name = Column(String(200), nullable=True)

    enrollments = relationship("Enrollment", back_populates="user", cascade="all, delete-orphan")


class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    activity_id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"))
    user_email = Column(String(200), ForeignKey("users.email", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    activity = relationship("Activity", back_populates="enrollments")
    user = relationship("User", back_populates="enrollments")
