from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Importamos el router desde tu estructura personalizada
from app.Controller.router import router as api_router
from app.Database.connection import engine, Base


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mi API con Estructura .NET",
    description="Estructura limpia usando Controller, DTOs y Services",
    version="1.0.0"
)

# Configuración de CORS (Símil app.UseCors)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registramos las rutas globales de tu carpeta Controller
app.include_router(api_router)

@app.get("/")
def root():
    return {"status": "Online", "message": "API levantada correctamente"}