from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.db import Base


class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    conversation_id = Column(
        String,
        index=True,
        nullable=True
    )

    role = Column(
        String
    )

    message = Column(
        Text
    )

    tool_used = Column(
        String,
        nullable=True
    )

    tool_output_summary = Column(
        Text,
        nullable=True
    )

    intent = Column(
        String,
        nullable=True
    )

    topic = Column(
        String,
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    user = relationship(
        "User"
    )