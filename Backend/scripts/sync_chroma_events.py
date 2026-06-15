import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.orm import selectinload

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.database import SessionLocal, init_db
from app.events.models import Event
from app.common.services.chroma_service import chroma_service

async def main() -> None:
    load_dotenv(project_root / ".env")
    await init_db()
    
    async with SessionLocal() as session:
        stmt = select(Event).where(Event.status == "approved").options(selectinload(Event.category))
        result = await session.execute(stmt)
        events = result.scalars().all()
        
        print(f"Found {len(events)} events to sync.")
        for event in events:
            try:
                # Sync category mapping
                if event.category:
                    await chroma_service.upsert_event_category(event.category.name, event.id)
                
                # Sync semantic search mapping
                title = event.title if event.title else ""
                description = event.description if event.description else ""
                await chroma_service.upsert_event_semantic(
                    title=title, 
                    description=description, 
                    event_id=event.id
                )
            except Exception as e:
                print(f"Failed to sync event {event.id}: {e}")
                
        print(f"Successfully synced {len(events)} events to ChromaDB.")

if __name__ == "__main__":
    asyncio.run(main())
