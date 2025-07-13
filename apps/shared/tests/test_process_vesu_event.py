# import pytest
# import time
# import asyncio
# from unittest.mock import Mock, AsyncMock, patch
# from datetime import datetime
# import logging
# from apps.data_handler.handlers.loan_states.vesu.events import VesuLoanEntity
# from apps.shared.background_tasks.data_handler.event_tasks import process_vesu_events


# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# @pytest.fixture
# def mock_vesu_entity():
#     """Fixture to mock VesuLoanEntity."""
#     mock = Mock(spec=VesuLoanEntity)
#     mock.last_processed_block = 654244  # Initial block
#     return mock

# @pytest.fixture
# def caplog(caplog):
#     """Fixture to capture log output."""
#     caplog.set_level(logging.INFO, logger="apps.shared.background_tasks.data_handler.event_tasks")
#     return caplog

# def test_process_vesu_events_success(mock_vesu_entity, caplog, monkeypatch):
#     """Test successful execution of process_vesu_events."""
#     # Mock VesuLoanEntity Class
#     monkeypatch.setattr(
#         "apps.shared.background_tasks.data_handler.event_tasks.VesuLoanEntity",
#         Mock(return_value=mock_vesu_entity)
#     )
#     # Mock update_positions_data
#     async def mock_update():
#         mock_vesu_entity.last_processed_block = 654249
#     mock_vesu_entity.update_positions_data = AsyncMock(side_effect=mock_update)

#     process_vesu_events()

#     assert "Starting Vesu event processing" in caplog.text
#     assert "Successfully processed Vesu events" in caplog.text
#     assert "Blocks: 654244 to 654249" in caplog.text
#     assert "(UTC)" in caplog.text
#     assert mock_vesu_entity.last_processed_block == 654249

# def test_process_vesu_events_value_error(mock_vesu_entity, caplog, monkeypatch):
#     """Test handling of ValueError."""
#     monkeypatch.setattr(
#         "apps.shared.background_tasks.data_handler.event_tasks.VesuLoanEntity",
#         Mock(return_value=mock_vesu_entity)
#     )
#     mock_vesu_entity.update_positions_data = AsyncMock(side_effect=ValueError("Failed to fetch events from Starknet"))
#     # Mock retry to prevent Retry exception
#     with patch.object(process_vesu_events, "retry", side_effect=Exception("Retry mocked")):
#         with pytest.raises(Exception, match="Retry mocked"):
#             process_vesu_events()

#     assert "Starting Vesu event processing" in caplog.text
#     assert "Error processing Vesu events" in caplog.text
#     assert "Failed to fetch events from Starknet" in caplog.text

# def test_process_vesu_events_unexpected_error(mock_vesu_entity, caplog, monkeypatch):
#     """Test handling of unexpected errors."""
#     monkeypatch.setattr(
#         "apps.shared.background_tasks.data_handler.event_tasks.VesuLoanEntity",
#         Mock(return_value=mock_vesu_entity)
#     )
#     mock_vesu_entity.update_positions_data = AsyncMock(side_effect=Exception("Unexpected Starknet error"))
#     # Mock retry to prevent Retry exception
#     with patch.object(process_vesu_events, "retry", side_effect=Exception("Retry mocked")):
#         with pytest.raises(Exception, match="Retry mocked"):
#             process_vesu_events()

#     assert "Starting Vesu event processing" in caplog.text
#     assert "Unexpected error processing Vesu events" in caplog.text
#     assert "Unexpected Starknet error" in caplog.text

# def test_process_vesu_events_scheduled(mock_vesu_entity, caplog, monkeypatch):
#     """Test periodic execution of process_vesu_events with a 3-second interval."""
#     chunk_size = 5
#     # Mock VesuLoanEntity
#     monkeypatch.setattr(
#         "apps.shared.background_tasks.data_handler.event_tasks.VesuLoanEntity",
#         Mock(return_value=mock_vesu_entity)
#     )

#     async def mock_update():
#         mock_vesu_entity.last_processed_block += chunk_size
#     mock_vesu_entity.update_positions_data = AsyncMock(side_effect=mock_update)

#     # Simulate 3 runs with 10-second intervals
#     initial_block = mock_vesu_entity.last_processed_block
#     num_runs = 3
#     for i in range(num_runs):
#         process_vesu_events()
#         if i < num_runs - 1:
#             time.sleep(10)


#     expected_blocks = [
#         (initial_block, initial_block + chunk_size),
#         (initial_block + chunk_size, initial_block + 2 * chunk_size),
#         (initial_block + 2 * chunk_size, initial_block + 3 * chunk_size)
#     ]
#     for start_block, end_block in expected_blocks:
#         assert f"Blocks: {start_block} to {end_block}" in caplog.text


#     assert mock_vesu_entity.last_processed_block == initial_block + num_runs * chunk_size
#     assert "Starting Vesu event processing" in caplog.text
#     assert "Successfully processed Vesu events" in caplog.text
#     assert "(UTC)" in caplog.text
