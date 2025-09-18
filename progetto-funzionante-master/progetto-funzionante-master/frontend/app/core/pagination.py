"""
Pagination utilities for efficient data handling
Implements cursor-based and offset-based pagination
"""

from typing import Optional, List, Dict, Any, TypeVar, Generic, Union
from dataclasses import dataclass
from sqlalchemy.orm import Query, Session
from sqlalchemy import desc, asc, func
import math
import base64
import json
from datetime import datetime

T = TypeVar('T')


@dataclass
class PaginationParams:
    """Pagination parameters for requests"""
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100
    cursor: Optional[str] = None
    direction: str = "next"  # "next" or "prev"

    def __post_init__(self):
        """Validate pagination parameters"""
        self.page = max(1, self.page)
        self.per_page = min(max(1, self.per_page), self.max_per_page)


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated response with metadata"""
    items: List[T]
    page: int
    per_page: int
    total: Optional[int] = None
    total_pages: Optional[int] = None
    has_next: bool = False
    has_prev: bool = False
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None

    @property
    def meta(self) -> Dict[str, Any]:
        """Pagination metadata"""
        return {
            "page": self.page,
            "per_page": self.per_page,
            "total": self.total,
            "total_pages": self.total_pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev,
            "next_cursor": self.next_cursor,
            "prev_cursor": self.prev_cursor
        }


class PaginationService:
    """
    Service for handling different pagination strategies
    Supports both offset-based and cursor-based pagination
    """

    @staticmethod
    def paginate_query(
        query: Query,
        pagination: PaginationParams,
        count_query: Optional[Query] = None,
        cursor_column: Optional[str] = "id",
        include_total: bool = True
    ) -> PaginatedResponse:
        """
        Paginate a SQLAlchemy query with offset-based pagination

        Args:
            query: Base query to paginate
            pagination: Pagination parameters
            count_query: Optional separate count query for performance
            cursor_column: Column to use for cursor pagination
            include_total: Whether to calculate total count

        Returns:
            PaginatedResponse with paginated data
        """
        # Calculate offset
        offset = (pagination.page - 1) * pagination.per_page

        # Get items with limit and offset
        items_query = query.offset(offset).limit(pagination.per_page + 1)  # +1 to check if there's a next page
        items = items_query.all()

        # Check if there are more items
        has_next = len(items) > pagination.per_page
        if has_next:
            items = items[:-1]  # Remove the extra item

        has_prev = pagination.page > 1

        # Calculate total and total_pages if requested
        total = None
        total_pages = None
        if include_total:
            if count_query:
                total = count_query.scalar()
            else:
                # Use the same query but count instead
                total = query.count()
            total_pages = math.ceil(total / pagination.per_page) if total > 0 else 0

        return PaginatedResponse(
            items=items,
            page=pagination.page,
            per_page=pagination.per_page,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
            has_prev=has_prev
        )

    @staticmethod
    def paginate_cursor(
        query: Query,
        pagination: PaginationParams,
        cursor_column: str = "id",
        cursor_direction: str = "desc"
    ) -> PaginatedResponse:
        """
        Paginate using cursor-based pagination (more efficient for large datasets)

        Args:
            query: Base query to paginate
            pagination: Pagination parameters with cursor
            cursor_column: Column to use for cursor
            cursor_direction: "asc" or "desc" ordering

        Returns:
            PaginatedResponse with cursor-based pagination
        """
        # Decode cursor if provided
        cursor_value = None
        if pagination.cursor:
            try:
                cursor_data = json.loads(base64.b64decode(pagination.cursor.encode()).decode())
                cursor_value = cursor_data.get("value")
            except Exception:
                cursor_value = None

        # Apply cursor filtering
        if cursor_value is not None:
            cursor_attr = getattr(query.column_descriptions[0]['entity'], cursor_column, None)
            if cursor_attr:
                if cursor_direction == "desc":
                    if pagination.direction == "next":
                        query = query.filter(cursor_attr < cursor_value)
                    else:  # prev
                        query = query.filter(cursor_attr > cursor_value)
                else:  # asc
                    if pagination.direction == "next":
                        query = query.filter(cursor_attr > cursor_value)
                    else:  # prev
                        query = query.filter(cursor_attr < cursor_value)

        # Apply ordering
        cursor_attr = getattr(query.column_descriptions[0]['entity'], cursor_column, None)
        if cursor_attr:
            if cursor_direction == "desc":
                query = query.order_by(desc(cursor_attr))
            else:
                query = query.order_by(asc(cursor_attr))

        # Get items with limit + 1 to check for next page
        items = query.limit(pagination.per_page + 1).all()

        # Check pagination state
        has_next = len(items) > pagination.per_page
        if has_next:
            items = items[:-1]

        has_prev = pagination.cursor is not None

        # Generate cursors
        next_cursor = None
        prev_cursor = None

        if items:
            if has_next:
                next_value = getattr(items[-1], cursor_column)
                next_cursor = base64.b64encode(
                    json.dumps({"value": next_value, "direction": "next"}).encode()
                ).decode()

            if has_prev:
                prev_value = getattr(items[0], cursor_column)
                prev_cursor = base64.b64encode(
                    json.dumps({"value": prev_value, "direction": "prev"}).encode()
                ).decode()

        return PaginatedResponse(
            items=items,
            page=pagination.page,
            per_page=pagination.per_page,
            has_next=has_next,
            has_prev=has_prev,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor
        )

    @staticmethod
    def paginate_signals_by_date(
        query: Query,
        pagination: PaginationParams,
        date_column: str = "created_at"
    ) -> PaginatedResponse:
        """
        Specialized pagination for signals using date-based cursor
        More efficient for time-series data

        Args:
            query: Base signals query
            pagination: Pagination parameters
            date_column: Date column for cursor pagination

        Returns:
            PaginatedResponse optimized for signals
        """
        return PaginationService.paginate_cursor(
            query=query,
            pagination=pagination,
            cursor_column=date_column,
            cursor_direction="desc"  # Most recent first
        )

    @staticmethod
    def create_count_query_optimization(query: Query) -> Query:
        """
        Create an optimized count query for large tables
        Removes unnecessary joins and selections

        Args:
            query: Original query

        Returns:
            Optimized count query
        """
        # Start with a new query from the same session
        from sqlalchemy.orm import Query as SQLQuery

        # Get the primary entity from the original query
        if hasattr(query, 'column_descriptions') and query.column_descriptions:
            entity = query.column_descriptions[0]['entity']

            # Create a simple count query
            count_query = query.session.query(func.count(entity.id))

            # Copy WHERE conditions from original query
            if hasattr(query, 'whereclause') and query.whereclause is not None:
                count_query = count_query.filter(query.whereclause)

            return count_query

        # Fallback to regular count
        return query

    @staticmethod
    def get_pagination_info(
        total_items: int,
        current_page: int,
        per_page: int
    ) -> Dict[str, Any]:
        """
        Calculate pagination information

        Args:
            total_items: Total number of items
            current_page: Current page number
            per_page: Items per page

        Returns:
            Dictionary with pagination info
        """
        total_pages = math.ceil(total_items / per_page) if total_items > 0 else 0
        start_item = (current_page - 1) * per_page + 1 if total_items > 0 else 0
        end_item = min(current_page * per_page, total_items)

        return {
            "total_items": total_items,
            "total_pages": total_pages,
            "current_page": current_page,
            "per_page": per_page,
            "start_item": start_item,
            "end_item": end_item,
            "has_previous": current_page > 1,
            "has_next": current_page < total_pages,
            "previous_page": current_page - 1 if current_page > 1 else None,
            "next_page": current_page + 1 if current_page < total_pages else None
        }


class StreamingPagination:
    """
    Streaming pagination for memory-efficient processing of large datasets
    Uses generator pattern to avoid loading all data into memory
    """

    @staticmethod
    def stream_query_results(
        query: Query,
        batch_size: int = 1000,
        order_by: Optional[str] = None
    ):
        """
        Stream query results in batches to avoid memory issues

        Args:
            query: SQLAlchemy query
            batch_size: Number of items per batch
            order_by: Column to order by for consistent results

        Yields:
            Batches of results
        """
        offset = 0

        # Apply ordering for consistent results
        if order_by:
            entity = query.column_descriptions[0]['entity']
            order_column = getattr(entity, order_by, None)
            if order_column:
                query = query.order_by(order_column)

        while True:
            batch = query.offset(offset).limit(batch_size).all()

            if not batch:
                break

            yield batch

            if len(batch) < batch_size:
                break

            offset += batch_size

    @staticmethod
    def process_large_dataset(
        query: Query,
        processor_func,
        batch_size: int = 1000,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process large dataset in batches with a custom processor function

        Args:
            query: SQLAlchemy query
            processor_func: Function to process each batch
            batch_size: Batch size for processing
            order_by: Column to order by

        Returns:
            Processing statistics
        """
        total_processed = 0
        batch_count = 0
        start_time = datetime.utcnow()

        try:
            for batch in StreamingPagination.stream_query_results(
                query, batch_size, order_by
            ):
                processor_func(batch)
                total_processed += len(batch)
                batch_count += 1

            end_time = datetime.utcnow()
            processing_time = (end_time - start_time).total_seconds()

            return {
                "success": True,
                "total_processed": total_processed,
                "batch_count": batch_count,
                "processing_time_seconds": processing_time,
                "items_per_second": total_processed / processing_time if processing_time > 0 else 0
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "total_processed": total_processed,
                "batch_count": batch_count
            }


# Utility functions for common pagination patterns

def paginate_signals(
    query: Query,
    page: int = 1,
    per_page: int = 20,
    use_cursor: bool = False
) -> PaginatedResponse:
    """
    Convenient function for paginating signals

    Args:
        query: Signals query
        page: Page number
        per_page: Items per page
        use_cursor: Use cursor-based pagination

    Returns:
        PaginatedResponse
    """
    pagination = PaginationParams(page=page, per_page=per_page)

    if use_cursor:
        return PaginationService.paginate_signals_by_date(query, pagination)
    else:
        return PaginationService.paginate_query(query, pagination)


def paginate_with_search(
    base_query: Query,
    search_term: Optional[str] = None,
    search_columns: Optional[List[str]] = None,
    page: int = 1,
    per_page: int = 20
) -> PaginatedResponse:
    """
    Paginate with search functionality

    Args:
        base_query: Base query to paginate
        search_term: Search term to filter by
        search_columns: Columns to search in
        page: Page number
        per_page: Items per page

    Returns:
        PaginatedResponse with search results
    """
    query = base_query

    # Apply search filter if provided
    if search_term and search_columns:
        search_filter = None
        entity = query.column_descriptions[0]['entity']

        for column_name in search_columns:
            column = getattr(entity, column_name, None)
            if column and hasattr(column.property, 'columns'):
                column_filter = column.ilike(f"%{search_term}%")
                if search_filter is None:
                    search_filter = column_filter
                else:
                    search_filter = search_filter | column_filter

        if search_filter is not None:
            query = query.filter(search_filter)

    pagination = PaginationParams(page=page, per_page=per_page)
    return PaginationService.paginate_query(query, pagination)