from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List, Optional, Any, Dict
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType], ABC):
    """
    Base repository class implementing common CRUD operations.
    """

    def __init__(self, model: type, db: Session):
        """
        Initialize repository with model and database session.

        Args:
            model: SQLAlchemy model class
            db: Database session
        """
        self.model = model
        self.db = db

    def get(self, id: Any, load_relationships: bool = True) -> Optional[ModelType]:
        """Get a single record by ID with optional relationship loading."""
        query = self.db.query(self.model)
        if load_relationships:
            query = self._add_eager_loading(query)
        return query.filter(self.model.id == id).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        load_relationships: bool = True
    ) -> List[ModelType]:
        """
        Get multiple records with pagination and filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            filters: Dictionary of column filters
            order_by: Column name to order by
            load_relationships: Enable eager loading of relationships
        """
        query = self.db.query(self.model)

        # Add eager loading if requested
        if load_relationships:
            query = self._add_eager_loading(query)

        # Apply filters
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, key).in_(value))
                    else:
                        query = query.filter(getattr(self.model, key) == value)

        # Apply ordering
        if order_by and hasattr(self.model, order_by):
            query = query.order_by(getattr(self.model, order_by))

        return query.offset(skip).limit(limit).all()

    def create(self, obj_in: CreateSchemaType) -> ModelType:
        """Create a new record."""
        obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
        db_obj = self.model(**obj_in_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: ModelType, obj_in: UpdateSchemaType) -> ModelType:
        """Update an existing record."""
        obj_data = obj_in.dict(exclude_unset=True) if hasattr(obj_in, 'dict') else obj_in

        for field, value in obj_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)

        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: Any) -> Optional[ModelType]:
        """Delete a record by ID."""
        obj = self.db.query(self.model).get(id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering."""
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    if isinstance(value, list):
                        query = query.filter(getattr(self.model, key).in_(value))
                    else:
                        query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def exists(self, id: Any) -> bool:
        """Check if a record exists by ID."""
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

    def get_by_field(self, field_name: str, field_value: Any) -> Optional[ModelType]:
        """Get a single record by any field."""
        if hasattr(self.model, field_name):
            return self.db.query(self.model).filter(getattr(self.model, field_name) == field_value).first()
        return None

    def get_multi_by_field(self, field_name: str, field_value: Any) -> List[ModelType]:
        """Get multiple records by any field."""
        if hasattr(self.model, field_name):
            return self.db.query(self.model).filter(getattr(self.model, field_name) == field_value).all()
        return []

    def bulk_create(self, objects: List[CreateSchemaType]) -> List[ModelType]:
        """Create multiple records in bulk."""
        db_objects = []
        for obj_in in objects:
            obj_in_data = obj_in.dict() if hasattr(obj_in, 'dict') else obj_in
            db_obj = self.model(**obj_in_data)
            db_objects.append(db_obj)

        self.db.add_all(db_objects)
        self.db.commit()

        for db_obj in db_objects:
            self.db.refresh(db_obj)

        return db_objects

    def filter_by_date_range(
        self,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        date_field: str = "created_at"
    ) -> List[ModelType]:
        """Filter records by date range."""
        query = self.db.query(self.model)

        if hasattr(self.model, date_field):
            date_column = getattr(self.model, date_field)

            if start_date:
                query = query.filter(date_column >= start_date)
            if end_date:
                query = query.filter(date_column <= end_date)

        return query.all()

    def _add_eager_loading(self, query):
        """Add eager loading options to query based on model type."""
        # This method can be overridden in specific repositories
        # for custom eager loading strategies
        return query