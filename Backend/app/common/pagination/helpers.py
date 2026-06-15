from math import ceil

from .meta import PaginationMeta


def build_pagination_meta(page: int, page_size: int, total: int) -> PaginationMeta:
    pages = ceil(total / page_size) if total else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
        has_next=page < pages,
    )
