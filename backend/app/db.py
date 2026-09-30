"""Database connection and session management."""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=settings.DEBUG
)

# Enable foreign keys for SQLite
if settings.DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency that yields a database session and ensures closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables and seed initial rule configurations."""
    import app.models  # noqa
    Base.metadata.create_all(bind=engine)
    
    # Initialize rule configs if not present
    from app.models import RuleConfigModel
    from app.engine.registry import load_rules
    
    db = SessionLocal()
    try:
        rules = load_rules()
        for rule in rules:
            existing = db.query(RuleConfigModel).filter_by(rule_name=rule.name).first()
            if not existing:
                config = RuleConfigModel(
                    rule_name=rule.name,
                    enabled=True,
                    params=rule.default_params,
                    weight=rule.weight
                )
                db.add(config)
        db.commit()
    finally:
        db.close()
