from sqlalchemy import create_engine, Column, Integer, String, BigInteger, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

# Таблица связи пользователей и интересов (многие ко многим)
user_interests = Table(
    'user_interests',
    Base.metadata,
    Column('user_id', BigInteger, ForeignKey('users.user_id')),
    Column('interest_id', Integer, ForeignKey('interests.id'))
)

class User(Base):
    __tablename__ = 'users'
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=True)
    name = Column(String)
    age = Column(Integer)
    district = Column(String)
    bio = Column(String, nullable=True)
    photo_file_id = Column(String, nullable=True)
    instagram = Column(String, nullable=True)
    registered_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    interests = relationship('Interest', secondary=user_interests, back_populates='users')
    created_events = relationship('Event', back_populates='creator')
    event_participations = relationship('EventParticipant', back_populates='user')
    notifications = relationship('NotificationHistory', back_populates='user')

class Interest(Base):
    __tablename__ = 'interests'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    category = Column(String)
    
    users = relationship('User', secondary=user_interests, back_populates='interests')
    events = relationship('Event', back_populates='category_rel')

class Event(Base):
    __tablename__ = 'events'
    
    event_id = Column(Integer, primary_key=True)
    creator_id = Column(BigInteger, ForeignKey('users.user_id'))
    title = Column(String)
    description = Column(String)
    category_id = Column(Integer, ForeignKey('interests.id'))
    photo_file_id = Column(String, nullable=True)
    address = Column(String)
    latitude = Column(String, nullable=True)
    longitude = Column(String, nullable=True)
    district = Column(String)
    event_date = Column(DateTime)
    price = Column(String)
    payment_method = Column(String, nullable=True)
    max_participants = Column(Integer, default=0)
    current_participants = Column(Integer, default=0)
    status = Column(String, default='pending')
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
    chat_link = Column(String, nullable=True)
    chat_id = Column(BigInteger, nullable=True)
    
    creator = relationship('User', back_populates='created_events')
    category_rel = relationship('Interest', back_populates='events')
    participants = relationship('EventParticipant', back_populates='event')
    notifications = relationship('NotificationHistory', back_populates='event')

class EventParticipant(Base):
    __tablename__ = 'event_participants'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'))
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    registered_at = Column(DateTime, default=datetime.now)
    status = Column(String, default='confirmed')
    
    user = relationship('User', back_populates='event_participations')
    event = relationship('Event', back_populates='participants')

class PromotionPackage(Base):
    __tablename__ = 'promotion_packages'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    duration_hours = Column(Integer)
    priority_level = Column(Integer)
    is_active = Column(Boolean, default=True)

class PromotedEvent(Base):
    __tablename__ = 'promoted_events'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'))
    package_id = Column(Integer, ForeignKey('promotion_packages.id'))
    promoted_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    payment_status = Column(String, default='pending')
    payment_id = Column(String, nullable=True)
    
    event = relationship('Event', backref='promotions')
    package = relationship('PromotionPackage')

class ModerationQueue(Base):
    __tablename__ = 'moderation_queue'
    
    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, ForeignKey('events.event_id'))
    submitted_at = Column(DateTime, default=datetime.now)
    reviewed_at = Column(DateTime, nullable=True)
    moderator_id = Column(BigInteger, nullable=True)
    comment = Column(String, nullable=True)
    status = Column(String, default='pending')

class Friend(Base):
    __tablename__ = 'friends'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    friend_id = Column(BigInteger, ForeignKey('users.user_id'))
    created_at = Column(DateTime, default=datetime.now)

# НОВАЯ ТАБЛИЦА
class NotificationHistory(Base):
    """История отправленных уведомлений"""
    __tablename__ = 'notification_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))
    event_id = Column(Integer, ForeignKey('events.event_id'))
    notification_type = Column(String)  # 'new_event' или 'reminder'
    sent_at = Column(DateTime, default=datetime.now)
    
    user = relationship('User', back_populates='notifications')
    event = relationship('Event', back_populates='notifications')