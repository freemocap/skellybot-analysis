from datetime import datetime
from typing import Type, TypeVar

from sqlmodel import SQLModel, Field, Session

BaseSQLModelType = TypeVar('BaseSQLModelType', bound='BaseSQLModel')



class BaseSQLModel(SQLModel):
    """Base model for all  entities with common fields."""
    id: int = Field(default=None, primary_key=True)
    name: str | None = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

    @classmethod
    def get_create_or_update(cls: Type[BaseSQLModelType],
                             session: Session,
                             db_id: int | str,
                             flush: bool = True,
                             **kwargs) -> BaseSQLModelType:
        """
        Get an existing record by id, create a new one if it doesn't exist,
        or update it if provided fields differ from current values.

        Args:
            session: SQLModel Session object
            db_id: Primary key value in the database
            flush: Whether to flush the session after adding the instance
            **kwargs: Fields to set/update on the model instance

        Returns:
            The model instance (either existing, new, or updated)
        """
        instance = session.get(cls, db_id)

        if not instance:
            # Create new instance if it doesn't exist
            instance = cls(id=db_id, **kwargs)
            session.add(instance)
            session.flush() if flush else None
            return instance

        # Check if any fields need updating
        needs_update = False
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None and getattr(instance, key) != value:
                setattr(instance, key, value)
                needs_update = True

        if needs_update:
            session.add(instance)
            if flush:
                session.flush()
                session.commit()

        return instance
