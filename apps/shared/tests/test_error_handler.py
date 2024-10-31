from uuid import uuid4, UUID

import pytest

from shared.error_handler.notifications import ErrorHandlerBot


class TestErrorHandlerBot:
    @pytest.fixture
    def error_handler(self):
        """Provides an ErrorHandlerBot instance for testing"""
        return ErrorHandlerBot(token=None)

    @pytest.fixture
    def mock_session(self):
        """Creates a mock session object for testing"""
        return str(uuid4())

    # Test Session Management
    def test_session_id_creation(self, error_handler):
        """Test that session ID is created and is a valid UUID"""
        assert error_handler.SESSION_ID is not None
        assert isinstance(error_handler.SESSION_ID, str)
        # Verify UUID format
        try:
            UUID(error_handler.SESSION_ID)
            is_valid_uuid = True
        except ValueError:
            is_valid_uuid = False
        assert is_valid_uuid

    def test_session_messages_initialization(self, error_handler):
        """Test that session messages are properly initialized"""
        assert isinstance(error_handler.SESSION_MESSAGES, dict)
        assert error_handler.SESSION_ID in error_handler.SESSION_MESSAGES
        assert isinstance(
            error_handler.SESSION_MESSAGES[error_handler.SESSION_ID], list
        )
        assert len(error_handler.SESSION_MESSAGES[error_handler.SESSION_ID]) == 0

    # Test Message Storage
    def test_add_message_to_session(self, error_handler):
        """Test adding a valid message to the session"""
        test_message = {"role": "user", "content": "Test message"}
        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].append(test_message)
        assert len(error_handler.SESSION_MESSAGES[error_handler.SESSION_ID]) == 1
        assert (
            error_handler.SESSION_MESSAGES[error_handler.SESSION_ID][0] == test_message
        )

    def test_add_invalid_message_format(self, error_handler):
        """Test adding message with invalid format"""
        invalid_message = "Invalid message format"  # This should be an instance of Message, not a str
        with pytest.raises(TypeError, match="Only Message instances are allowed"):
            error_handler.add_message(invalid_message)

    # Test Session Cleanup
    def test_clear_session_messages(self, error_handler):
        """Test clearing messages from a session"""
        # Add some test messages first
        test_messages = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Message 2"},
        ]
        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].extend(test_messages)

        # Clear messages
        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].clear()
        assert len(error_handler.SESSION_MESSAGES[error_handler.SESSION_ID]) == 0

    def test_delete_session(self, error_handler, mock_session):
        """Test deleting an entire session"""
        # Create a new session
        error_handler.SESSION_MESSAGES[mock_session] = []

        # Delete it
        del error_handler.SESSION_MESSAGES[mock_session]
        assert mock_session not in error_handler.SESSION_MESSAGES

    # Test Session Validation
    def test_invalid_session_access(self, error_handler):
        """Test accessing an invalid session"""
        invalid_session = str(uuid4())
        with pytest.raises(KeyError):
            _ = error_handler.SESSION_MESSAGES[invalid_session]

    # Test Message Validation
    def test_message_format_validation(self, error_handler):
        """Test various message format validations"""
        from shared.error_handler.notifications import Message
        # Define a valid Message instance
        valid_message = Message(text="Valid message", is_sent=False)

        # Define invalid messages
        invalid_messages = [
            None,  # None value should raise TypeError
            "Invalid string instead of Message",  # String instead of Message object should raise TypeError
        ]

        # Valid message should work (as a Message instance)
        error_handler.add_message(valid_message)
        assert valid_message in error_handler.SESSION_MESSAGES[error_handler.SESSION_ID]

        # Invalid messages should raise exceptions
        for invalid_msg in invalid_messages:
            with pytest.raises((ValueError, TypeError)):
                error_handler.add_message(invalid_msg)

    # Test Concurrent Access
    @pytest.mark.asyncio
    async def test_concurrent_message_addition(self, error_handler):
        """Test adding messages concurrently"""
        import asyncio
        from asyncio import Lock

        lock = Lock()

        async def add_message(message):
            async with lock:
                error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].append(
                    {"role": "user", "content": message}
                )
            await asyncio.sleep(0.1)

        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].clear()
        # Create multiple concurrent tasks
        tasks = [add_message(f"Message {i}") for i in range(5)]
        await asyncio.gather(*tasks)

        assert len(error_handler.SESSION_MESSAGES[error_handler.SESSION_ID]) == 5

    # Test Memory Management
    def test_memory_limit(self, error_handler):
        """Test handling of memory limits"""
        large_message = {"role": "user", "content": "x" * 1024 * 1024}

        # Add multiple large messages
        for _ in range(100):
            try:
                error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].append(
                    large_message
                )
            except MemoryError:
                # Should raise MemoryError when limit is reached
                break

        # Clean up
        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].clear()

    # Test Edge Cases
    def test_empty_session_operations(self, error_handler):
        """Test operations on empty session"""
        # Clear should work on empty session
        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].clear()
        assert len(error_handler.SESSION_MESSAGES[error_handler.SESSION_ID]) == 0

        # Accessing elements should raise IndexError
        with pytest.raises(IndexError):
            _ = error_handler.SESSION_MESSAGES[error_handler.SESSION_ID][0]

    def test_special_characters_in_messages(self, error_handler):
        """Test handling of special characters in messages"""
        special_chars_message = {
            "role": "user",
            "content": "!@#$%^&*()_+{}[]|\\:;\"'<>,.?/~`",
        }
        error_handler.SESSION_MESSAGES[error_handler.SESSION_ID].append(
            special_chars_message
        )
        assert (
            error_handler.SESSION_MESSAGES[error_handler.SESSION_ID][-1]
            == special_chars_message
        )
