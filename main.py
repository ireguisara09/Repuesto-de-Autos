"""
Módulo Principal de la Aplicación (main.py)
Instancia FastAPI, gestiona CORS, conexion asincrona y expone el CRUD con Motor
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from bson import ObjectId
from datetime import datetime

from models import Repuesto, RepuestoCreate, RepuestoUpdate
from database import coleccion_repuestos, verificar_conexion

# Instancia principal de FastAPI
app = FastAPI(
    title="API Repuesto de Autos - SENA ADSO",
    description="API RESTful asíncrona con FastAPI y MongoDB (FARM Stack)",
    version="1.0.0"
)

# Configuración de CORS para permitir conexión con clientes Frontend (React, Angular, etc)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Evento de inicio de servidor 
@app.on_event("startup")
async def startup_db_client():
    await verificar_conexion()

# =============================
# ENDPOINTS RESTful ASÍNCRONOS
# =============================

@app.get("/", tags=["Raíz"])
async def root():
    return {
        "mensaje": "Bienvenido a la API de Repuesto de Autos (SENA ADSO)",
        "documentacion": "/docs"
    }

@app.post(
    "/repuestos",
    response_model=Repuesto,
    status_code=status.HTTP_201_CREATED,
    tags=["Repuestos"],
    summary="Crear un nuevo repuesto en MongoDB"
)
async def create_repuesto(tarea_in: RepuestoCreate):
   
    # 1. Validar que noe xista otra tarea con el mismo título
    repuesto_existente = await coleccion_repuestos.find_one({"Repuesto": tarea_in.Repuesto})
    if repuesto_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un repuesto registrado con ese nombre '{tarea_in.Repuesto}'"
        )
    # 2. Preparar el diccionario del documento
    nuevo_repuesto = tarea_in.model_dump()
    nuevo_repuesto["fecha_creacion"] = datetime.now()

    # 3. Insertar asíncronamente en MongoDB
    resultado = await coleccion_repuestos.insert_one(nuevo_repuesto)

    # 4. Recuperar el documento recién creado por su _id ObjectId
    repuesto_creado = await coleccion_repuestos.find_one({"_id": resultado.inserted_id})
    return repuesto_creado

@app.get(
    "/repuestos",
    response_model=List[Repuesto],
    status_code=status.HTTP_200_OK,
    tags=["Repuestos"],
    summary="Listar todos los repuestos creados"
)
async def get_repuestos():
    repuestos = []
    # Usar cursor asíncrono de Motor}
    cursor = coleccion_repuestos.find()
    async for documento in cursor:
        repuestos.append(documento)
    return repuestos

@app.get(
    "/repuestos/{id}",
    response_model=Repuesto,
    status_code=status.HTTP_200_OK,
    tags=["Repuestos"],
    summary="Buscar repuesto por ObjectId"
)
async def get_repuesto_por_id(id: str):
   
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido de MongoDB"
        )

    repuesto = await coleccion_repuestos.find_one({"_id": ObjectId(id)})
    if repuesto:
        return repuesto

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"El repuesto con ID '{id}' no fue encontrado en la base de datos"
    )

@app.put(
    "/repuestos/{id}",
    response_model=Repuesto,
    status_code=status.HTTP_200_OK,
    tags=["Repuestos"],
    summary="Actualizar estado o campos de un Repuesto"
)
async def update_repuesto(id: str, repuesto_update: RepuestoUpdate):

    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId Válido"
        )

    # Estraer solo los datos enviados en la petición 
    datos_a_actualizar = repuesto_update.model_dump(exclude_unset=True)

    if len(datos_a_actualizar) >= 1:
        resultado_actualizacion = await coleccion_repuestos.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos_a_actualizar}
        )

        if resultado_actualizacion.modified_count == 1 or resultado_actualizacion.matched_count == 1:
            repuesto_modificado = await coleccion_repuestos.find_one({"_id": ObjectId(id)})
            return repuesto_modificado

    # Si no se modificó o no s encontró el ID
    repuesto_existente = await coleccion_repuestos.find_one({"_id": ObjectId(id)})
    if repuesto_existente: 
        return repuesto_existente

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible actualizar. La tarea con ID '{id}' no existe"
    )

@app.delete(
    "/repuestos/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Repuestos"],
    summary="Eliminar repuesto de MongoDB"
)
async def delete_repuesto(id: str):
    
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId Válido"
        )
    resultado_eliminacion = await coleccion_repuestos.delete_one({"_id": ObjectId(id)})

    if resultado_eliminacion.deleted_count == 1:
        return {"mensaje": f"Repuesto con ID '{id}' eliminado exitosamente de MongoDB"}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible eliminar. El repuesto con ID '{id}' no existe en la base de datos"
    )