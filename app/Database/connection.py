from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Creamos una base de datos local SQLite que se guardará en un archivo llamado 'ventas.db'
SQLALCHEMY_DATABASE_URL = "sqlite:///./ventas.db"

engine = create_engine(
    # 'check_same_thread' solo es necesario para SQLite
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# El equivalente al DBContext de .NET para inyectar la sesión por Request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()