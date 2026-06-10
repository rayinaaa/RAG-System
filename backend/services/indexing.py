from concurrent.futures import ThreadPoolExecutor

from backend.services.config import settings


indexing_executor = ThreadPoolExecutor(
    max_workers=max(1, settings.indexing_workers),
    thread_name_prefix="document-indexer",
)
