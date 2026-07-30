from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.Database.connection import engine, Base
from app.Models.sale import Sale  # Registra la tabla en Base.metadata
from app.Controller.router import router as api_router

# Crear las tablas en la base de datos si no existen
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Visualización Ventas",
    description="Backend modular para Dashboard de Ingresos y Clientes",
    version="1.0.0"
)

# Configuración de CORS segura para Next.js
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # <-- Se define explícitamente el frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos el router centralizado que agrupa todos los sub-controladores
app.include_router(api_router)

@app.get("/", tags=["Health Check"])
def root():
    return {"status": "Online", "message": "API corriendo correctamente"}