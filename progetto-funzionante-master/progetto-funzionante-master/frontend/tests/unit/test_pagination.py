"""
Unit tests for pagination utilities.
"""

import pytest
import math
import json
import base64
from unittest.mock import MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc, func

from app.core.pagination import (
    PaginationParams,
    PaginatedResponse,
    PaginationService,
    StreamingPagination,
    paginate_signals,
    paginate_with_search
)


class TestPaginationParams:
    """Test cases for PaginationParams."""

    @pytest.mark.unit
    def test_pagination_params_default(self):
        """Test PaginationParams with default values."""
        params = PaginationParams()

        assert params.page == 1
        assert params.per_page == 20
        assert params.max_per_page == 100
        assert params.cursor is None
        assert params.direction == "next"

    @pytest.mark.unit
    def test_pagination_params_validation_page_too_low(self):
        """Test PaginationParams validates page too low."""
        params = PaginationParams(page=0)

        assert params.page == 1  # Should be adjusted to minimum

    @pytest.mark.unit
    def test_pagination_params_validation_page_too_high(self):
        """Test PaginationParams validates page within limits."""
        params = PaginationParams(page=999)

        assert params.page == 999  # No upper limit on page number

    @pytest.mark.unit
    def test_pagination_params_validation_per_page_too_low(self):
        """Test PaginationParams validates per_page too low."""
        params = PaginationParams(per_page=0)

        assert params.per_page == 1  # Should be adjusted to minimum

    @pytest.mark.unit
    def test_pagination_params_validation_per_page_too_high(self):
        """Test PaginationParams validates per_page too high."""
        params = PaginationParams(per_page=200, max_per_page=50)

        assert params.per_page == 50  # Should be adjusted to maximum

    @pytest.mark.unit
    def test_pagination_params_with_cursor(self):
        """Test PaginationParams with cursor."""
        cursor_data = {"value": 123, "direction": "next"}
        cursor_str = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        params = PaginationParams(cursor=cursor_str, direction="prev")

        assert params.cursor == cursor_str
        assert params.direction == "prev"


class TestPaginatedResponse:
    """Test cases for PaginatedResponse."""

    @pytest.mark.unit
    def test_paginated_response_basic(self):
        """Test PaginatedResponse with basic data."""
        items = [1, 2, 3]
        response = PaginatedResponse(
            items=items,
            page=1,
            per_page=20,
            total=100,
            total_pages=5,
            has_next=True,
            has_prev=False
        )

        assert response.items == items
        assert response.page == 1
        assert response.per_page == 20
        assert response.total == 100
        assert response.total_pages == 5
        assert response.has_next is True
        assert response.has_prev is False

    @pytest.mark.unit
    def test_paginated_response_meta_property(self):
        """Test PaginatedResponse meta property."""
        items = [1, 2, 3]
        response = PaginatedResponse(
            items=items,
            page=2,
            per_page=10,
            total=50,
            total_pages=5,
            has_next=True,
            has_prev=True,
            next_cursor="next_cursor",
            prev_cursor="prev_cursor"
        )

        meta = response.meta

        assert meta["page"] == 2
        assert meta["per_page"] == 10
        assert meta["total"] == 50
        assert meta["total_pages"] == 5
        assert meta["has_next"] is True
        assert meta["has_prev"] is True
        assert meta["next_cursor"] == "next_cursor"
        assert meta["prev_cursor"] == "prev_cursor"

    @pytest.mark.unit
    def test_paginated_response_no_total(self):
        """Test PaginatedResponse without total count."""
        items = [1, 2, 3]
        response = PaginatedResponse(
            items=items,
            page=1,
            per_page=20
        )

        assert response.total is None
        assert response.total_pages is None


class TestPaginationService:
    """Test cases for PaginationService."""

    @pytest.mark.unit
    def test_paginate_query_basic(self):
        """Test basic query pagination."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_items
        mock_query.count.return_value = 100

        pagination = PaginationParams(page=1, per_page=10)

        # Act
        result = PaginationService.paginate_query(mock_query, pagination)

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.page == 1
        assert result.per_page == 10
        assert result.total == 100
        assert result.total_pages == 10
        assert result.has_next is False
        assert result.has_prev is False

        # Verify query calls
        mock_query.offset.assert_called_once_with(0)  # (1-1)*10
        mock_query.limit.assert_called_once_with(11)  # per_page + 1
        mock_query.count.assert_called_once()

    @pytest.mark.unit
    def test_paginate_query_has_next(self):
        """Test query pagination when there are more items."""
        # Arrange
        mock_query = MagicMock()
        # Return 11 items (per_page + 1) to indicate there's a next page
        mock_items = list(range(11))
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_items
        mock_query.count.return_value = 100

        pagination = PaginationParams(page=1, per_page=10)

        # Act
        result = PaginationService.paginate_query(mock_query, pagination)

        # Assert
        assert len(result.items) == 10  # Should be truncated
        assert result.has_next is True
        assert result.has_prev is False

    @pytest.mark.unit
    def test_paginate_query_has_prev(self):
        """Test query pagination when there are previous items."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_items
        mock_query.count.return_value = 100

        pagination = PaginationParams(page=2, per_page=10)

        # Act
        result = PaginationService.paginate_query(mock_query, pagination)

        # Assert
        assert result.has_prev is True
        assert result.page == 2

        # Verify correct offset
        mock_query.offset.assert_called_once_with(10)  # (2-1)*10

    @pytest.mark.unit
    def test_paginate_query_no_total(self):
        """Test query pagination without total count."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_items

        pagination = PaginationParams(page=1, per_page=10)

        # Act
        result = PaginationService.paginate_query(mock_query, pagination, include_total=False)

        # Assert
        assert result.total is None
        assert result.total_pages is None
        mock_query.count.assert_not_called()

    @pytest.mark.unit
    def test_paginate_query_with_count_query(self):
        """Test query pagination with separate count query."""
        # Arrange
        mock_query = MagicMock()
        mock_count_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_items
        mock_count_query.scalar.return_value = 50

        pagination = PaginationParams(page=1, per_page=10)

        # Act
        result = PaginationService.paginate_query(
            mock_query, pagination, count_query=mock_count_query
        )

        # Assert
        assert result.total == 50
        assert result.total_pages == 5
        mock_count_query.scalar.assert_called_once()
        mock_query.count.assert_not_called()

    @pytest.mark.unit
    def test_paginate_cursor_no_cursor(self):
        """Test cursor pagination without cursor (first page)."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.limit.return_value.all.return_value = mock_items

        # Mock column descriptions
        mock_entity = MagicMock()
        mock_id_attr = MagicMock()
        setattr(mock_entity, 'id', mock_id_attr)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        pagination = PaginationParams(page=1, per_page=10)

        # Act
        result = PaginationService.paginate_cursor(
            mock_query, pagination, cursor_column="id", cursor_direction="desc"
        )

        # Assert
        assert isinstance(result, PaginatedResponse)
        assert result.items == mock_items
        assert result.has_next is False
        assert result.has_prev is False

        # Verify ordering was applied
        mock_query.order_by.assert_called_once_with(desc(mock_id_attr))

    @pytest.mark.unit
    def test_paginate_cursor_with_cursor(self):
        """Test cursor pagination with cursor."""
        # Arrange
        cursor_data = {"value": 123, "direction": "next"}
        cursor_str = base64.b64encode(json.dumps(cursor_data).encode()).decode()

        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.limit.return_value.all.return_value = mock_items

        # Mock column descriptions and attribute
        mock_entity = MagicMock()
        mock_id_attr = MagicMock()
        setattr(mock_entity, 'id', mock_id_attr)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        pagination = PaginationParams(page=1, per_page=10, cursor=cursor_str)

        # Act
        result = PaginationService.paginate_cursor(
            mock_query, pagination, cursor_column="id", cursor_direction="desc"
        )

        # Assert
        assert isinstance(result, PaginatedResponse)

        # Verify cursor filtering was applied
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once_with(desc(mock_id_attr))

    @pytest.mark.unit
    def test_paginate_cursor_has_next_generates_cursor(self):
        """Test cursor pagination generates next cursor when there are more items."""
        # Arrange
        mock_item1 = MagicMock()
        mock_item1.id = 123
        mock_item2 = MagicMock()
        mock_item2.id = 124
        mock_items = [mock_item1, mock_item2]  # per_page + 1 to indicate next page

        mock_query = MagicMock()
        mock_query.limit.return_value.all.return_value = mock_items

        # Mock column descriptions and attribute
        mock_entity = MagicMock()
        mock_id_attr = MagicMock()
        setattr(mock_entity, 'id', mock_id_attr)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        pagination = PaginationParams(page=1, per_page=1)

        # Act
        result = PaginationService.paginate_cursor(
            mock_query, pagination, cursor_column="id", cursor_direction="desc"
        )

        # Assert
        assert len(result.items) == 1  # Should be truncated
        assert result.has_next is True
        assert result.next_cursor is not None
        assert result.prev_cursor is None

        # Verify cursor format
        cursor_data = json.loads(base64.b64decode(result.next_cursor.encode()).decode())
        assert cursor_data["value"] == 123  # ID of last item
        assert cursor_data["direction"] == "next"

    @pytest.mark.unit
    def test_paginate_cursor_invalid_cursor(self):
        """Test cursor pagination with invalid cursor (should not crash)."""
        # Arrange
        invalid_cursor = "invalid_cursor_data"

        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.limit.return_value.all.return_value = mock_items

        # Mock column descriptions and attribute
        mock_entity = MagicMock()
        mock_id_attr = MagicMock()
        setattr(mock_entity, 'id', mock_id_attr)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        pagination = PaginationParams(page=1, per_page=10, cursor=invalid_cursor)

        # Act
        result = PaginationService.paginate_cursor(
            mock_query, pagination, cursor_column="id", cursor_direction="desc"
        )

        # Assert
        assert isinstance(result, PaginatedResponse)
        # Should still work even with invalid cursor

    @pytest.mark.unit
    def test_paginate_signals_by_date(self):
        """Test specialized signals pagination by date."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_query.limit.return_value.all.return_value = mock_items

        # Mock column descriptions and attribute
        mock_entity = MagicMock()
        mock_created_at_attr = MagicMock()
        setattr(mock_entity, 'created_at', mock_created_at_attr)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        pagination = PaginationParams(page=1, per_page=10)

        # Act
        result = PaginationService.paginate_signals_by_date(
            mock_query, pagination, date_column="created_at"
        )

        # Assert
        assert isinstance(result, PaginatedResponse)

        # Verify it calls paginate_cursor with correct parameters
        with patch.object(PaginationService, 'paginate_cursor') as mock_paginate_cursor:
            PaginationService.paginate_signals_by_date(mock_query, pagination)
            mock_paginate_cursor.assert_called_once_with(
                query=mock_query,
                pagination=pagination,
                cursor_column="created_at",
                cursor_direction="desc"
            )

    @pytest.mark.unit
    def test_create_count_query_optimization(self):
        """Test count query optimization."""
        # Arrange
        mock_session = MagicMock()
        mock_entity = MagicMock()
        mock_whereclause = MagicMock()

        mock_query = MagicMock()
        mock_query.session = mock_session
        mock_query.column_descriptions = [{'entity': mock_entity}]
        mock_query.whereclause = mock_whereclause

        # Act
        result = PaginationService.create_count_query_optimization(mock_query)

        # Assert
        mock_session.query.assert_called_once_with(func.count(mock_entity.id))
        optimized_query = mock_session.query.return_value
        optimized_query.filter.assert_called_once_with(mock_whereclause)

    @pytest.mark.unit
    def test_create_count_query_optimization_fallback(self):
        """Test count query optimization fallback."""
        # Arrange
        mock_query = MagicMock()
        mock_query.column_descriptions = []  # No column descriptions

        # Act
        result = PaginationService.create_count_query_optimization(mock_query)

        # Assert
        assert result == mock_query  # Should return original query

    @pytest.mark.unit
    def test_get_pagination_info(self):
        """Test pagination info calculation."""
        # Arrange
        total_items = 100
        current_page = 3
        per_page = 20

        # Act
        result = PaginationService.get_pagination_info(
            total_items, current_page, per_page
        )

        # Assert
        assert result["total_items"] == 100
        assert result["total_pages"] == 5
        assert result["current_page"] == 3
        assert result["per_page"] == 20
        assert result["start_item"] == 41
        assert result["end_item"] == 60
        assert result["has_previous"] is True
        assert result["has_next"] is True
        assert result["previous_page"] == 2
        assert result["next_page"] == 4

    @pytest.mark.unit
    def test_get_pagination_info_first_page(self):
        """Test pagination info for first page."""
        # Arrange
        total_items = 50
        current_page = 1
        per_page = 10

        # Act
        result = PaginationService.get_pagination_info(
            total_items, current_page, per_page
        )

        # Assert
        assert result["start_item"] == 1
        assert result["end_item"] == 10
        assert result["has_previous"] is False
        assert result["previous_page"] is None

    @pytest.mark.unit
    def test_get_pagination_info_last_page(self):
        """Test pagination info for last page."""
        # Arrange
        total_items = 45
        current_page = 5
        per_page = 10

        # Act
        result = PaginationService.get_pagination_info(
            total_items, current_page, per_page
        )

        # Assert
        assert result["start_item"] == 41
        assert result["end_item"] == 45
        assert result["has_next"] is False
        assert result["next_page"] is None

    @pytest.mark.unit
    def test_get_pagination_info_no_items(self):
        """Test pagination info with no items."""
        # Arrange
        total_items = 0
        current_page = 1
        per_page = 10

        # Act
        result = PaginationService.get_pagination_info(
            total_items, current_page, per_page
        )

        # Assert
        assert result["total_items"] == 0
        assert result["total_pages"] == 0
        assert result["start_item"] == 0
        assert result["end_item"] == 0
        assert result["has_previous"] is False
        assert result["has_next"] is False


class TestStreamingPagination:
    """Test cases for StreamingPagination."""

    @pytest.mark.unit
    def test_stream_query_results_single_batch(self):
        """Test streaming query results with single batch."""
        # Arrange
        mock_query = MagicMock()
        mock_batch = [1, 2, 3]
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_batch

        # Mock column descriptions
        mock_entity = MagicMock()
        mock_query.column_descriptions = [{'entity': mock_entity}]

        # Act
        result = list(StreamingPagination.stream_query_results(mock_query, batch_size=5))

        # Assert
        assert result == [mock_batch]  # Single batch

        # Verify query calls
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(5)

    @pytest.mark.unit
    def test_stream_query_results_multiple_batches(self):
        """Test streaming query results with multiple batches."""
        # Arrange
        mock_query = MagicMock()
        batches = [[1, 2], [3, 4], [5]]  # Last batch is smaller
        mock_query.offset.return_value.limit.return_value.all.side_effect = batches

        # Mock column descriptions
        mock_entity = MagicMock()
        mock_query.column_descriptions = [{'entity': mock_entity}]

        # Act
        result = list(StreamingPagination.stream_query_results(mock_query, batch_size=2))

        # Assert
        assert result == batches

        # Verify query calls
        expected_calls = [
            ((0, 2), {}),  # First batch
            ((2, 2), {}),  # Second batch
            ((4, 2), {}),  # Third batch (will return only 1 item)
        ]
        actual_calls = []
        for call in mock_query.offset.call_args_list:
            actual_calls.append((call[0], call[1]))
        assert actual_calls == expected_calls

    @pytest.mark.unit
    def test_stream_query_results_with_ordering(self):
        """Test streaming query results with ordering."""
        # Arrange
        mock_query = MagicMock()
        mock_batch = [1, 2, 3]
        mock_query.offset.return_value.limit.return_value.all.return_value = mock_batch

        # Mock column descriptions and attribute
        mock_entity = MagicMock()
        mock_id_attr = MagicMock()
        setattr(mock_entity, 'id', mock_id_attr)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        # Act
        result = list(StreamingPagination.stream_query_results(
            mock_query, batch_size=5, order_by="id"
        ))

        # Assert
        assert result == [[mock_batch]]

        # Verify ordering was applied
        mock_query.order_by.assert_called_once_with(mock_id_attr)

    @pytest.mark.unit
    def test_process_large_dataset_success(self):
        """Test successful processing of large dataset."""
        # Arrange
        mock_query = MagicMock()
        batches = [[1, 2, 3], [4, 5, 6]]
        mock_query.offset.return_value.limit.return_value.all.side_effect = batches

        # Mock column descriptions
        mock_entity = MagicMock()
        mock_query.column_descriptions = [{'entity': mock_entity}]

        processed_items = []

        def processor_func(batch):
            processed_items.extend(batch)

        # Act
        result = StreamingPagination.process_large_dataset(
            mock_query, processor_func, batch_size=3, order_by="id"
        )

        # Assert
        assert result["success"] is True
        assert result["total_processed"] == 6
        assert result["batch_count"] == 2
        assert result["processing_time_seconds"] > 0
        assert result["items_per_second"] > 0
        assert processed_items == [1, 2, 3, 4, 5, 6]

    @pytest.mark.unit
    def test_process_large_dataset_error(self):
        """Test processing large dataset with error."""
        # Arrange
        mock_query = MagicMock()
        mock_query.offset.return_value.limit.return_value.all.side_effect = Exception("Database error")

        # Mock column descriptions
        mock_entity = MagicMock()
        mock_query.column_descriptions = [{'entity': mock_entity}]

        def processor_func(batch):
            pass

        # Act
        result = StreamingPagination.process_large_dataset(
            mock_query, processor_func, batch_size=3
        )

        # Assert
        assert result["success"] is False
        assert "error" in result
        assert result["total_processed"] == 0
        assert result["batch_count"] == 0


class TestUtilityFunctions:
    """Test cases for pagination utility functions."""

    @pytest.mark.unit
    def test_paginate_signals_offset_based(self):
        """Test paginate_signals with offset-based pagination."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_response = PaginatedResponse(
            items=mock_items, page=1, per_page=10
        )

        with patch.object(PaginationService, 'paginate_query', return_value=mock_response) as mock_paginate:
            # Act
            result = paginate_signals(mock_query, page=1, per_page=10, use_cursor=False)

            # Assert
            assert result == mock_response
            mock_paginate.assert_called_once()

            # Verify call parameters
            call_args = mock_paginate.call_args
            assert call_args[0][0] == mock_query  # query
            assert call_args[1].page == 1
            assert call_args[1].per_page == 10

    @pytest.mark.unit
    def test_paginate_signals_cursor_based(self):
        """Test paginate_signals with cursor-based pagination."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_response = PaginatedResponse(
            items=mock_items, page=1, per_page=10
        )

        with patch.object(PaginationService, 'paginate_signals_by_date', return_value=mock_response) as mock_paginate:
            # Act
            result = paginate_signals(mock_query, page=1, per_page=10, use_cursor=True)

            # Assert
            assert result == mock_response
            mock_paginate.assert_called_once()

    @pytest.mark.unit
    def test_paginate_with_search_no_search(self):
        """Test paginate_with_search without search term."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_response = PaginatedResponse(
            items=mock_items, page=1, per_page=10
        )

        with patch.object(PaginationService, 'paginate_query', return_value=mock_response) as mock_paginate:
            # Act
            result = paginate_with_search(
                mock_query, search_term=None, page=1, per_page=10
            )

            # Assert
            assert result == mock_response
            mock_paginate.assert_called_once()

            # Verify no filter was applied
            mock_query.filter.assert_not_called()

    @pytest.mark.unit
    def test_paginate_with_search_with_search(self):
        """Test paginate_with_search with search term."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_response = PaginatedResponse(
            items=mock_items, page=1, per_page=10
        )

        # Mock entity and columns
        mock_entity = MagicMock()
        mock_col1 = MagicMock()
        mock_col2 = MagicMock()
        setattr(mock_entity, 'name', mock_col1)
        setattr(mock_entity, 'description', mock_col2)
        mock_query.column_descriptions = [{'entity': mock_entity}]

        with patch.object(PaginationService, 'paginate_query', return_value=mock_response) as mock_paginate:
            # Act
            result = paginate_with_search(
                mock_query,
                search_term="test",
                search_columns=["name", "description"],
                page=1,
                per_page=10
            )

            # Assert
            assert result == mock_response
            mock_paginate.assert_called_once()

            # Verify search filter was applied
            mock_query.filter.assert_called_once()

            # Verify ilike calls
            mock_col1.ilike.assert_called_once_with("%test%")
            mock_col2.ilike.assert_called_once_with("%test%")

    @pytest.mark.unit
    def test_paginate_with_search_invalid_columns(self):
        """Test paginate_with_search with invalid search columns."""
        # Arrange
        mock_query = MagicMock()
        mock_items = [1, 2, 3]
        mock_response = PaginatedResponse(
            items=mock_items, page=1, per_page=10
        )

        # Mock entity without the requested columns
        mock_entity = MagicMock()
        mock_query.column_descriptions = [{'entity': mock_entity}]

        with patch.object(PaginationService, 'paginate_query', return_value=mock_response) as mock_paginate:
            # Act
            result = paginate_with_search(
                mock_query,
                search_term="test",
                search_columns=["nonexistent_column"],
                page=1,
                per_page=10
            )

            # Assert
            assert result == mock_response
            mock_paginate.assert_called_once()

            # No filter should be applied for invalid columns
            mock_query.filter.assert_not_called()