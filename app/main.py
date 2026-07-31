"""
Punto de Entrada Principal de la Aplicación FastAPI.

Este módulo inicializa la instancia principal de FastAPI, ejecuta la creación
automática de tablas en la base de datos relacional mediante SQLAlchemy,
configura la política de intercambio de recursos de origen cruzado (CORS) 
para permitir la comunicación segura con el frontend (Next.js) y registra 
el enrutador central de la API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.Database.connection import engine, Base
from app.Models.sale import Sale  # Importante: Registra el modelo Sale en Base.metadata antes de crear las tablas
from app.Controller.router import router as api_router

# Generación automática de tablas en la base de datos al arrancar si aún no existen
Base.metadata.create_all(bind=engine)

# Instanciación y configuración de metadatos globales de la API
app = FastAPI(
    title="API Visualización Ventas",
    description="Backend modular para Dashboard de Ingresos y Clientes",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE CORS (Cross-Origin Resource Sharing)
# -----------------------------------------------------------------------------
# Lista de orígenes permitidos (Servidor de desarrollo e instancias de Next.js)
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Middleware para gestión de peticiones entre dominios/puertos distintos
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Define explícitamente las URLs de origen permitidas
    allow_credentials=True,
    allow_methods=["*"],    # Permite todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Permite todos los encabezados personalizados en las peticiones
)

# Registramos el enrutador centralizado que expone los módulos /api/v1/
app.include_router(api_router)


# -----------------------------------------------------------------------------
# ENDPOINTS DE DIAGNÓSTICO Y SALUD
# -----------------------------------------------------------------------------
@app.get("/", tags=["Health Check"])
def root():
    """
    Endpoint de comprobación de estado y conectividad (Health Check).

    Permite verificar de forma rápida si la API está arriba y respondiendo
    solicitudes HTTP correctamente.

    ### Respuestas:
    - **200 OK**: Retorna un objeto con el estado operativo de la API.
    """
    return {"status": "Online", "message": "API corriendo correctamente"}