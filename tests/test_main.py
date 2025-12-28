"""
Tests for the main module.
"""

from test_handler.main import hello_world

def test_hello_world():
    assert hello_world() == "Hello from test_handler!"
