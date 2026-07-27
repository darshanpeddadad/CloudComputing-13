from typing import List

from pydantic import BaseModel

from app.common.pagination import PaginationMeta, build_pagination_meta

from .event_edit_request import EventEditRequestResponse


class PaginatedEventEditRequestsResponse(BaseModel):
    items: List[EventEditRequestResponse]
    pagination: PaginationMeta

    @staticmethod
    def pagination_meta(page: int, page_size: int, total: int) -> PaginationMeta:
        return build_pagination_meta(page, page_size, total)
