"""
Configuración de la Base de Datos y Gestión de Sesiones (SQLAlchemy).

Este módulo establece la conexión con la base de datos relacional, configura
el motor de persistencia (engine), la fábrica de sesiones (`SessionLocal`), 
la clase base declarativa para los modelos ORM (`Base`) y el generador de 
sesiones inyectable por petición HTTP (`get_db`).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Cadena de conexión para la base de datos local SQLite ('ventas.db')
SQLALCHEMY_DATABASE_URL = "sqlite:///./ventas.db"

# Motor de conexión de SQLAlchemy.
# 'check_same_thread: False' es requerido por SQLite para permitir que múltiples
# hilos concurrentes compartan la conexión en peticiones asíncronas de FastAPI.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Fábrica de sesiones de base de datos.
# - autocommit=False: Mantiene el control explícito de las transacciones (commit/rollback).
# - autoflush=False: Previene descargas automáticas a la DB antes de ejecutar consultas.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base declarativa requerida para definir las entidades/modelos ORM
Base = declarative_base()


def get_db():
    """
    Generador de dependencia de FastAPI que administra el ciclo de vida de la sesión de DB.

    Funciona como un equivalente al patrón DBContext / Scoped Lifetime en .NET:
    1. Instancia una sesión de base de datos limpia (`SessionLocal`).
    2. Cede el control (`yield`) al endpoint o servicio consumidor.
    3. Asegura el cierre adecuado de la conexión (`db.close()`) en la cláusula `finally`,
       garantizando la liberación de recursos incluso si ocurre una excepción.

    Yields:
        Session: Sesión activa de SQLAlchemy para operaciones de lectura/escritura.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()