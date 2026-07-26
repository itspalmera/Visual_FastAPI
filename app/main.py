from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Corregido: controller en minúscula para coincidir con tu carpeta física
from app.Controller.endpoints.sales import router as sales_router
from app.Database.connection import engine, Base

# Asegura la autocreación de la tabla sales_registry en SQLite
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API Visualización Ventas",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Conectamos las rutas de tu controlador de ventas
app.include_router(sales_router)