
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import auth, catalogos, cupos, despachos, alertas
from app.core.config import Settings
from app.core.database import get_db

settings = Settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health(db=Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "estado": "ok",
        "base_de_datos": "conectada"
    }


app.include_router(auth.router)
app.include_router(catalogos.router)
app.include_router(cupos.router)
app.include_router(despachos.router)
app.include_router(alertas.router)
