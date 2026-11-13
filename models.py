"""
Módulo de Modelos de Datos (models.py)
Define esquemas de Pydantic y adaptadores para ObjectId de MongoDb
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Annotated
from datetime import datetime
from bson import ObjectId
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema

class _ObjectIdPydanticAnnotation:
    """Adaptador para validar y serializar ObjectId de MongoDB en Pydantic v2"""
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID invalido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )

# Tipo de dato reutilizable para Pydantic
PyObjectId = Annotated[str, _ObjectIdPydanticAnnotation]

class RepuestoBase(BaseModel):
    Repuesto: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Nombre descriptivo del repuesto",
        example="Pastillas de freno delanteras"
    )
    modelo_compatible: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Lista de marcas, modelos y años compatibles con el repuesto.",
        examples=[["Toyota Corolla 2018-2023", "Nissan Sentra 2020", "Mazda 3 2019-2022"]]
    )
    precio: float = Field(
        gt=0,
        description="Precio unitario del repuesto (debe ser mayor a 0).",
        examples=[45.99]
    )
    disponible: bool = Field(
        default=False,
        description="El repuesto se encuentra disponible o no se encuentra diponible"
    )

class RepuestoCreate(RepuestoBase):
    """Modelo utilizado para recibir solicitudes POST de creación"""
    pass

class Repuesto(RepuestoBase):
    """Modelo utilizado para devolver una tarea con sus datos de MongoDB"""
    id: PyObjectId = Field(alias="_id", description="Identificador único ObjectId de MongoDB")
    fecha_creacion: datetime

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

class RepuestoUpdate(BaseModel):
    """Modelo utilizado para recibir actualizaciones parciales de una tarea"""
    Repuesto: str = Field(
        ...,
        min_length=3,
        max_length=150,
        description="Nombre descriptivo del repuesto",
        example="Pastillas de freno delanteras"
    )
    modelo_compatible: list[str] = Field(
        default_factory=list,
        max_length=50,
        description="Lista de marcas, modelos y años compatibles con el repuesto.",
        examples=[["Toyota Corolla 2018-2023", "Nissan Sentra 2020", "Mazda 3 2019-2022"]]
    )
    precio: float = Field(
        gt=0,
        description="Precio unitario del repuesto (debe ser mayor a 0).",
        examples=[45.99]
    )
    disponible: bool = Field(
        default=False,
        description="El repuesto se encuentra disponible o no se encuentra diponible"
    )
    
