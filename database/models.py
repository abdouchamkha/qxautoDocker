"""
SQLAlchemy models for the multi-user trading platform.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
import bcrypt
import os
from cryptography.fernet import Fernet

db = SQLAlchemy()


class User(db.Model):
    """User model for platform authentication and management."""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    subscriptions = relationship('Subscription', back_populates='user', cascade='all, delete-orphan')
    quotex_accounts = relationship('QuotexAccount', back_populates='user', cascade='all, delete-orphan')
    trading_sessions = relationship('TradingSession', back_populates='user', cascade='all, delete-orphan')
    api_tokens = relationship('ApiToken', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Hash and set the user's password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    @property
    def active_subscription(self):
        """Get the user's currently active subscription."""
        return Subscription.query.filter_by(
            user_id=self.id, 
            is_active=True
        ).filter(
            Subscription.end_date > datetime.now(timezone.utc)
        ).first()
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_sensitive:
            data['active_subscription'] = self.active_subscription.to_dict() if self.active_subscription else None
        return data


class Subscription(db.Model):
    """Subscription model for user access tiers."""
    
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subscription_type = Column(String(50), nullable=False)  # 'basic', 'premium', 'vip'
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    max_accounts = Column(Integer, default=1, nullable=False)
    max_sessions = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='subscriptions')
    
    @property
    def is_expired(self):
        """Check if the subscription has expired."""
        end_date = self.end_date
        if end_date.tzinfo is None:
            # Assume naive datetimes are in UTC
            end_date = end_date.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > end_date
    
    @property
    def days_remaining(self):
        """Calculate days remaining in subscription."""
        now = datetime.now(timezone.utc)
        end_date = self.end_date
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)
        if self.is_expired:
            return 0
        delta = end_date - now
        return max(0, delta.days)
    
    def to_dict(self):
        """Convert subscription to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subscription_type': self.subscription_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'days_remaining': self.days_remaining,
            'max_accounts': self.max_accounts,
            'max_sessions': self.max_sessions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QuotexAccount(db.Model):
    """Quotex trading account model with encrypted credentials."""
    
    __tablename__ = 'quotex_accounts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    email = Column(String(100), nullable=False)
    password_encrypted = Column(Text, nullable=False)
    account_type = Column(String(10), nullable=False)  # 'demo' or 'real'
    account_name = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    last_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='quotex_accounts')
    trading_sessions = relationship('TradingSession', back_populates='account', cascade='all, delete-orphan')
    
    def set_password(self, password: str):
        """Encrypt and store the Quotex account password."""
        encryption_key = os.getenv('DATABASE_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("DATABASE_ENCRYPTION_KEY environment variable not set")
        
        cipher = Fernet(encryption_key.encode())
        self.password_encrypted = cipher.encrypt(password.encode()).decode()
    
    def get_password(self) -> str:
        """Decrypt and return the Quotex account password."""
        encryption_key = os.getenv('DATABASE_ENCRYPTION_KEY')
        if not encryption_key:
            raise ValueError("DATABASE_ENCRYPTION_KEY environment variable not set")
        
        cipher = Fernet(encryption_key.encode())
        return cipher.decrypt(self.password_encrypted.encode()).decode()
    
    def to_dict(self, include_sensitive=False):
        """Convert account to dictionary representation."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'account_type': self.account_type,
            'account_name': self.account_name,
            'is_active': self.is_active,
            'last_balance': self.last_balance,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        if include_sensitive:
            try:
                data['password'] = self.get_password()
            except Exception:
                data['password'] = None
        return data


class TradingSession(db.Model):
    """Trading session model for managing individual trading configurations."""
    
    __tablename__ = 'trading_sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('quotex_accounts.id'), nullable=False)
    session_name = Column(String(100))
    trade_amount = Column(Float, nullable=False)
    gale_limit = Column(Integer, default=1, nullable=False)
    stop_profit = Column(Float)
    stop_loss = Column(Float)
    is_active = Column(Boolean, default=False, nullable=False)
    current_gale_count = Column(Integer, default=0, nullable=False)
    net_profit = Column(Float, default=0.0, nullable=False)
    total_trades = Column(Integer, default=0, nullable=False)
    winning_trades = Column(Integer, default=0, nullable=False)
    losing_trades = Column(Integer, default=0, nullable=False)
    session_start_time = Column(DateTime)
    session_end_time = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='trading_sessions')
    account = relationship('QuotexAccount', back_populates='trading_sessions')
    trades = relationship('Trade', back_populates='session', cascade='all, delete-orphan')
    
    @property
    def win_rate(self):
        """Calculate the win rate percentage."""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    @property
    def session_duration(self):
        """Calculate session duration in seconds."""
        if not self.session_start_time:
            return 0
        
        end_time = self.session_end_time or datetime.now(timezone.utc)
        delta = end_time - self.session_start_time
        return delta.total_seconds()
    
    @property
    def profit_status(self):
        """Get profit/loss status relative to limits."""
        status = "active"
        
        if self.stop_profit and self.net_profit >= self.stop_profit:
            status = "stop_profit_reached"
        elif self.stop_loss and self.net_profit <= -self.stop_loss:
            status = "stop_loss_reached"
        
        return status
    
    def update_stats(self, won: bool, profit_amount: float):
        """Update session statistics after a trade."""
        self.total_trades += 1
        if won:
            self.winning_trades += 1
            self.net_profit += profit_amount
        else:
            self.losing_trades += 1
            self.net_profit -= profit_amount
        
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self):
        """Convert session to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_id': self.account_id,
            'session_name': self.session_name,
            'trade_amount': self.trade_amount,
            'gale_limit': self.gale_limit,
            'stop_profit': self.stop_profit,
            'stop_loss': self.stop_loss,
            'is_active': self.is_active,
            'current_gale_count': self.current_gale_count,
            'net_profit': self.net_profit,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'session_duration': self.session_duration,
            'profit_status': self.profit_status,
            'session_start_time': self.session_start_time.isoformat() if self.session_start_time else None,
            'session_end_time': self.session_end_time.isoformat() if self.session_end_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Trade(db.Model):
    """Trade history model for tracking individual trades."""
    
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('trading_sessions.id'), nullable=False)
    asset = Column(String(50), nullable=False)
    direction = Column(String(10), nullable=False)  # 'call' or 'put'
    amount = Column(Float, nullable=False)
    duration = Column(Integer, nullable=False)
    is_gale = Column(Boolean, default=False, nullable=False)
    gale_sequence = Column(Integer, default=0, nullable=False)
    result = Column(String(10))  # 'win', 'loss', 'pending'
    profit_loss = Column(Float, default=0.0, nullable=False)
    open_time = Column(DateTime, nullable=False)
    close_time = Column(DateTime)
    signal_source = Column(String(100))  # Telegram channel or manual
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    session = relationship('TradingSession', back_populates='trades')
    
    @property
    def trade_duration_seconds(self):
        """Calculate actual trade duration in seconds."""
        if not self.close_time:
            return None
        delta = self.close_time - self.open_time
        return delta.total_seconds()
    
    def to_dict(self):
        """Convert trade to dictionary representation."""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'asset': self.asset,
            'direction': self.direction,
            'amount': self.amount,
            'duration': self.duration,
            'is_gale': self.is_gale,
            'gale_sequence': self.gale_sequence,
            'result': self.result,
            'profit_loss': self.profit_loss,
            'trade_duration_seconds': self.trade_duration_seconds,
            'open_time': self.open_time.isoformat() if self.open_time else None,
            'close_time': self.close_time.isoformat() if self.close_time else None,
            'signal_source': self.signal_source,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ApiToken(db.Model):
    """API token model for authentication management."""
    
    __tablename__ = 'api_tokens'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='api_tokens')
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return datetime.now(timezone.utc) > self.expires_at
    
    def to_dict(self):
        """Convert token to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 