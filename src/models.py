"""SQLAlchemy 모델 정의."""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON, LargeBinary, ForeignKey
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy import create_engine

from .config import config

Base = declarative_base()


class Repo(Base):
    """GitHub 레포 메타데이터."""
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False, index=True)
    full_name = Column(String, nullable=False)  # owner/name
    description = Column(Text)
    language = Column(String)
    topics = Column(JSON, default=list)
    stars = Column(Integer, default=0)
    forks = Column(Integer, default=0)
    is_fork = Column(Integer, default=0)  # boolean as int
    is_archived = Column(Integer, default=0)
    created_at = Column(DateTime)
    pushed_at = Column(DateTime)  # 마지막 커밋 push 시점
    readme = Column(Text)
    package_files = Column(JSON, default=dict)  # {"package.json": "...", "requirements.txt": "..."}
    fetched_at = Column(DateTime, default=datetime.utcnow)

    analysis = relationship("Analysis", back_populates="repo", uselist=False)


class Analysis(Base):
    """레포별 분석 결과 (Phase 2에서 채움)."""
    __tablename__ = "analysis"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), unique=True, nullable=False)
    domain = Column(String)  # 임상AI, 풀스택, 인프라, 학습용 등
    form = Column(String)    # 웹앱, CLI, 라이브러리, PWA 등
    status = Column(String)  # active, archived, abandoned
    embedding = Column(LargeBinary)  # numpy array as bytes
    cluster_id = Column(Integer)
    analyzed_at = Column(DateTime, default=datetime.utcnow)

    repo = relationship("Repo", back_populates="analysis")


class Recommendation(Base):
    """추천 결과 이력 (Phase 3 결과)."""
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    payload = Column(JSON)  # 전체 추천 결과 JSON
    acted_on = Column(JSON, default=list)  # 나중에 수동으로 "이건 만들었음" 표시


def init_db() -> None:
    """DB 초기화 (테이블 생성)."""
    engine = create_engine(config.DB_URL)
    Base.metadata.create_all(engine)


def get_session():
    """세션 팩토리."""
    engine = create_engine(config.DB_URL)
    Session = sessionmaker(bind=engine)
    return Session()
