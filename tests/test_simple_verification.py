"""
Simple test file for VS Code test discovery verification.
This file contains basic tests that VS Code should easily discover.
"""

def test_simple_math():
    """Test basic math operations."""
    assert 1 + 1 == 2
    assert 2 * 3 == 6
    assert 10 / 2 == 5

def test_string_operations():
    """Test string operations."""
    assert "hello".upper() == "HELLO"
    assert "WORLD".lower() == "world"
    assert len("test") == 4

class TestBasicFunctionality:
    """Basic test class for VS Code discovery."""
    
    def test_list_operations(self):
        """Test list operations."""
        my_list = [1, 2, 3]
        assert len(my_list) == 3
        assert my_list[0] == 1
        assert 2 in my_list
    
    def test_dict_operations(self):
        """Test dictionary operations."""
        my_dict = {"key": "value", "number": 42}
        assert my_dict["key"] == "value"
        assert my_dict["number"] == 42
        assert "key" in my_dict

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])