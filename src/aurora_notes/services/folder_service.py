"""Folder management service."""

from typing import List, Optional
from uuid import UUID
from sqlmodel import Session, select
from ..models.base import Folder, create_db_engine


class FolderService:
    """Handles folder operations."""
    
    def __init__(self):
        self.engine = create_db_engine()
    
    def create_folder(self, name: str) -> Optional[Folder]:
        """Create new folder."""
        with Session(self.engine) as session:
            # Check if exists
            existing = session.exec(
                select(Folder).where(Folder.name == name)
            ).first()
            
            if existing:
                return None
            
            folder = Folder(name=name)
            session.add(folder)
            session.commit()
            session.refresh(folder)
            return folder
    
    def get_all_folders(self) -> List[Folder]:
        """Get all folders."""
        with Session(self.engine) as session:
            return list(session.exec(select(Folder)).all())
    
    def rename_folder(self, folder_id: UUID, new_name: str) -> Optional[Folder]:
        """Rename folder."""
        with Session(self.engine) as session:
            folder = session.get(Folder, folder_id)
            if not folder:
                return None
            
            # Check if new name exists
            existing = session.exec(
                select(Folder).where(
                    Folder.name == new_name,
                    Folder.id != folder_id
                )
            ).first()
            
            if existing:
                return None
            
            folder.name = new_name
            session.add(folder)
            session.commit()
            session.refresh(folder)
            return folder
    
    def delete_folder(self, folder_id: UUID) -> bool:
        """Delete folder (notes remain but become unfiled)."""
        with Session(self.engine) as session:
            folder = session.get(Folder, folder_id)
            if folder:
                session.delete(folder)
                session.commit()
                return True
            return False