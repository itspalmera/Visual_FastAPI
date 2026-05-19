from fastapi import APIRouter, status
from pydantic import BaseModel

# Inicializamos el enrutador
router = APIRouter(prefix="/api/v1", tags=["Endpoints Base"])

# Un DTO rápido de prueba usando Pydantic (Luego lo moverás a tu carpeta DTOs)
class TestInput(BaseModel):
    nombre: str
    activo: bool

@router.get("/test")
def get_test():
    return {"message": "¡Conexión exitosa desde el Controller!"}

@router.post("/test", status_code=status.HTTP_201_CREATED)
def post_test(data: TestInput):
    return {
        "status": "Recibido",
        "tu_nombre": data.nombre,
        "estado": "Usuario Activo" if data.activo else "Usuario Inactivo"
    }