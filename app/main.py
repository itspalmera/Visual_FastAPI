from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.Controller.router import router as api_router
from app.Database.connection import engine, Base

# Creación de tablas en SQLite
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Visualización Ventas",
    description="Backend modular para Dashboard de Ingresos y Clientes",
    version="1.0.0"
)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos el router centralizado que agrupa todos los sub-controladores
app.include_router(api_router)

@app.get("/", tags=["Health Check"])
def root():
    return {"status": "Online", "message": "API corriendo correctamente"}