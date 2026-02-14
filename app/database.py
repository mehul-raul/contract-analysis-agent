from sqlalchemy import Index, create_engine, Column, Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
from pgvector.sqlalchemy import Vector
from datetime import datetime, timezone

engine = create_engine(settings.DATABASE_URL)

Base = declarative_base()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Contract(Base):
    __tablename__ = "contracts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    upload_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    num_chunks = Column(Integer, default=0)

class ContractChunk(Base):
    __tablename__ = "contract_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    embedding = Column(Vector(3072))  # COZ 3072-dim embeddings from GEMINI model

    __table_args__ = (
        Index(
            'idx_chunk_fts',
            text("to_tsvector('english', chunk_text)"),
            postgresql_using='gin'
        ),
    )

# Function to create tables
def init_db():
    """Create all tables"""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")


# Function to get database session
def get_db():
    """Get database session for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def drop_db():
    """Drop all tables"""
    Base.metadata.drop_all(bind=engine)
    print("🗑️ All tables dropped")