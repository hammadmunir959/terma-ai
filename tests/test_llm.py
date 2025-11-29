"""Tests for LLM client"""

import pytest
from unittest.mock import Mock, patch
from termai.core.llm import LLMClient


class TestLLMClient:
    """Test the LLM client functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            self.client = LLMClient()

    @patch('termai.core.llm.OpenAI')
    def test_initialization(self, mock_openai):
        """Test client initialization"""
        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()

            assert client.api_key == 'test-key'
            assert 'model' in client.config
            assert 'temperature' in client.config

    @patch('termai.core.llm.load_dotenv')
    def test_missing_api_key(self, mock_load_dotenv):
        """Test error when API key is missing"""
        mock_load_dotenv.return_value = None  # Don't load .env file
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="API_KEY environment variable not found"):
                LLMClient()

    @patch('termai.core.llm.OpenAI')
    def test_generate_commands_success(self, mock_openai_class):
        """Test successful command generation"""
        # Mock the OpenAI client and response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"commands": ["ls -la"], "explanations": ["List files"], "safe": true}'
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.generate_commands("list files")

            assert result["commands"] == ["ls -la"]
            assert result["explanations"] == ["List files"]
            assert result["safe"] == True
            assert result["error"] is None

    @patch('termai.core.llm.OpenAI')
    def test_generate_commands_api_error(self, mock_openai_class):
        """Test handling of API errors"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.generate_commands("list files")

            assert "error" in result
            assert "API Error" in result["error"]
            assert result["commands"] == []
            assert result["explanations"] == []

    @patch('termai.core.llm.OpenAI')
    def test_generate_commands_invalid_json(self, mock_openai_class):
        """Test handling of invalid JSON responses"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.generate_commands("list files")

            assert "error" in result
            assert "Invalid JSON" in result["error"]

    @patch('termai.core.llm.OpenAI')
    def test_test_connection_success(self, mock_openai_class):
        """Test successful connection test"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.test_connection()

            assert result == True

    @patch('termai.core.llm.OpenAI')
    def test_test_connection_failure(self, mock_openai_class):
        """Test failed connection test"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Connection failed")

        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            result = client.test_connection()

            assert result == False

    def test_system_prompt_content(self):
        """Test that system prompt contains safety instructions"""
        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            prompt = client._get_system_prompt()

            assert "SAFE" in prompt.upper()
            assert "DANGER" in prompt.upper()
            assert "NEVER" in prompt
            assert "JSON" in prompt

    def test_user_prompt_format(self):
        """Test user prompt formatting"""
        with patch.dict('os.environ', {'API_KEY': 'test-key'}):
            client = LLMClient()
            prompt = client._get_user_prompt("test query")

            assert "test query" in prompt
            assert "bash commands" in prompt
