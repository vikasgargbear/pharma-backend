"""
Generic CRUD operations base class
Reduces 90% of repetitive CRUD code
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

try:
    from ..database import Base
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).
        
        **Parameters**
        * `model`: A SQLAlchemy model class
        * `schema`: A Pydantic model (schema) class
        """
        self.model = model
        # Find the primary key column dynamically
        self.pk_column = None
        for column in model.__table__.columns:
            if column.primary_key:
                self.pk_column = column
                break
        if self.pk_column is None:
            raise ValueError(f"No primary key found for model {model.__name__}")

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """Get a single record by ID"""
        return db.query(self.model).filter(self.pk_column == id).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """Get multiple records with optional filtering"""
        query = db.query(self.model)
        
        # Apply filters if provided
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record"""
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """Update an existing record"""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> ModelType:
        """Delete a record"""
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj
    
    def get_by_field(self, db: Session, field_name: str, field_value: Any) -> Optional[ModelType]:
        """Get record by any field"""
        if hasattr(self.model, field_name):
            return db.query(self.model).filter(getattr(self.model, field_name) == field_value).first()
        return None
    
    def get_active(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Get active records (if model has is_active field)"""
        if hasattr(self.model, 'is_active'):
            return db.query(self.model).filter(self.model.is_active == True).offset(skip).limit(limit).all()
        return self.get_multi(db, skip=skip, limit=limit)
    
    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        query = db.query(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
        
        return query.count()
    
    def exists(self, db: Session, id: Any) -> bool:
        """Check if record exists"""
        return db.query(self.model).filter(self.pk_column == id).first() is not None


# Factory function to create CRUD instances
def create_crud(model: Type[ModelType]) -> CRUDBase:
    """Factory function to create CRUD instance for any model"""
    return CRUDBase(model) 