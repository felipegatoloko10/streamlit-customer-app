from typing import Generic, TypeVar, Type, List, Optional
from sqlmodel import Session, select, SQLModel

T = TypeVar("T", bound=SQLModel)

class BaseRepository(Generic[T]):
    def __init__(self, session: Session, model: Type[T]):
        self.session = session
        self.model = model

    def get(self, id: int) -> Optional[T]:
        """Get entity by ID. Override in subclass to add eager loading if needed."""
        return self.session.get(self.model, id)

    def get_all(self) -> List[T]:
        statement = select(self.model)
        return self.session.exec(statement).all()

    def create(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity: T):
        self.session.delete(entity)
        self.session.commit()
