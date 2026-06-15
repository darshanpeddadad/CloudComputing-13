import logging
import random
from typing import List
import chromadb

logger = logging.getLogger(__name__)

class ChromaService:
    _instance = None
    
    # Distance thresholds
    SEARCH_DISTANCE_THRESHOLD = 1.4
    RECOMMEND_DISTANCE_THRESHOLD = 1.0

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, data_path: str = "./chroma_db"):
        if not hasattr(self, 'initialized'):
            try:
                self.client = chromadb.PersistentClient(path=data_path)
                # Stores categories mapping to multiple event IDs
                self.collection = self.client.get_or_create_collection(name="event_categories")
                # Stores individual events for semantic search
                self.semantic_collection = self.client.get_or_create_collection(name="events_semantic")
                self.initialized = True
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB: {e}")
                self.initialized = False

    async def upsert_event_semantic(self, title: str, description: str, event_id: str) -> None:
        if not self.initialized:
            return
            
        try:
            document_text = f"{title}\n{description}"
            self.semantic_collection.upsert(
                ids=[event_id],
                documents=[document_text]
            )
        except Exception as e:
            logger.error(f"Error upserting event semantic in ChromaDB for event {event_id}: {e}")

    async def delete_event_semantic(self, event_id: str) -> None:
        if not self.initialized:
            return
            
        try:
            self.semantic_collection.delete(ids=[event_id])
        except Exception as e:
            logger.error(f"Error deleting event semantic in ChromaDB for event {event_id}: {e}")

    async def search_events_semantically(self, query: str, limit: int = 10) -> List[str]:
        if not self.initialized or not query:
            return []
            
        try:
            results = self.semantic_collection.query(
                query_texts=[query],
                n_results=limit
            )
            if results and results.get("ids") and results["ids"]:
                ids = results["ids"][0]
                # Filter by distance threshold to ensure relevance
                distances_lists = results.get("distances")
                distances = distances_lists[0] if distances_lists else [0.0] * len(ids)
                filtered_ids = [doc_id for doc_id, dist in zip(ids, distances) if dist < self.SEARCH_DISTANCE_THRESHOLD]
                return filtered_ids
            return []
        except Exception as e:
            logger.error(f"Error semantic querying ChromaDB: {e}")
            return []

    async def upsert_event_category(self, category_name: str, event_id: str) -> None:
        if not self.initialized:
            return

        try:
            result = self.collection.get(ids=[category_name])
            
            # If the category already exists, append the new event ID
            if result and result.get("ids"):
                metadata = result.get("metadatas")[0]
                existing_events = metadata.get("event_ids", "")
                
                events_list = existing_events.split(",") if existing_events else []
                if event_id not in events_list:
                    events_list.append(event_id)
                    metadata["event_ids"] = ",".join(events_list)
                    
                    self.collection.update(
                        ids=[category_name],
                        metadatas=[metadata]
                    )
            else:
                self.collection.add(
                    ids=[category_name],
                    documents=[category_name],
                    metadatas=[{"event_ids": event_id}]
                )
        except Exception as e:
            logger.error(f"Error upserting event category in ChromaDB: {e}")

    async def remove_event_from_category(self, category_name: str, event_id: str) -> None:
        if not self.initialized:
            return

        try:
            result = self.collection.get(ids=[category_name])
            if result and result.get("ids"):
                metadata = result.get("metadatas")[0]
                existing_events = metadata.get("event_ids", "")
                events_list = existing_events.split(",") if existing_events else []
                
                if event_id in events_list:
                    events_list.remove(event_id)
                    
                    # Update category if it still has events, otherwise delete the category entirely
                    if events_list:
                        metadata["event_ids"] = ",".join(events_list)
                        self.collection.update(
                            ids=[category_name],
                            metadatas=[metadata]
                        )
                    else:
                        self.collection.delete(ids=[category_name])
        except Exception as e:
            logger.error(f"Error removing event from category in ChromaDB: {e}")

    async def get_recommended_event_ids(self, interests: List[str], limit: int = 10) -> List[str]:
        if not self.initialized or not interests:
            return []
            
        try:
            results = self.collection.query(
                query_texts=interests,
                n_results=limit
            )
            
            category_events = []
            seen_event_lists = set()
            metadatas = results.get("metadatas", [])
            distances_lists = results.get("distances", [])
            
            if not distances_lists or len(distances_lists) != len(metadatas):
                distances_lists = [[0.0] * len(m) for m in metadatas]
                
            for res_meta_list, res_dist_list in zip(metadatas, distances_lists):
                for metadata, distance in zip(res_meta_list, res_dist_list):
                    if distance < self.RECOMMEND_DISTANCE_THRESHOLD:
                        event_ids_str = metadata.get("event_ids", "")
                        if event_ids_str and event_ids_str not in seen_event_lists:
                            seen_event_lists.add(event_ids_str)
                            events = event_ids_str.split(",")
                            random.shuffle(events)
                            category_events.append(events)

            # Shuffle categories to ensure random distribution
            random.shuffle(category_events)
            
            final_events = []
            seen_events = set()
            
            # Round-robin selection across different categories
            max_len = max((len(evts) for evts in category_events), default=0)
            for i in range(max_len):
                for evts in category_events:
                    if i < len(evts):
                        evt = evts[i]
                        if evt not in seen_events:
                            seen_events.add(evt)
                            final_events.append(evt)

            return final_events[:limit]
        except Exception as e:
            logger.error(f"Error querying ChromaDB: {e}")
            return []

chroma_service = ChromaService()
