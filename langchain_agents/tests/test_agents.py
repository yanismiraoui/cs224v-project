import pytest
import asyncio
from unittest.mock import Mock, patch
from ..agent import JobApplicationAgent
from ..tools import WebsiteGeneratorTool, ProfileOptimizerTool
from ..custom_together_llm import TogetherLLM

# Test data
SAMPLE_WEBSITE_DATA = {
    "name": "John Doe",
    "title": "Software Engineer",
    "experience": ["Company A - Senior Dev", "Company B - Junior Dev"],
    "education": ["MS Computer Science"],
    "skills": ["Python", "JavaScript", "Cloud Computing"]
}

SAMPLE_LINKEDIN_DATA = {
    "headline": "Software Engineer",
    "about": "5 years of experience in web development",
    "experience": ["Full Stack Developer at Tech Corp"],
    "skills": ["React", "Node.js", "Python"]
}

@pytest.fixture
def mock_together_api():
    """Mock Together AI API responses"""
    with patch('together.Complete.create') as mock_create:
        mock_create.return_value = {
            'output': {
                'choices': [{
                    'text': 'Mocked response from Together AI'
                }]
            }
        }
        yield mock_create

@pytest.fixture
async def agent():
    """Create a test agent instance"""
    return JobApplicationAgent(api_key="test_api_key")

# Unit Tests
class TestTogetherLLM:
    async def test_llm_initialization(self):
        """Test LLM initialization"""
        llm = TogetherLLM(api_key="test_key")
        assert llm.model_name == "togethercomputer/llama-2-70b-chat"
        assert llm.temperature == 0.7
        
    async def test_llm_call(self, mock_together_api):
        """Test LLM call functionality"""
        llm = TogetherLLM(api_key="test_key")
        response = await llm._call("Test prompt")
        assert response == "Mocked response from Together AI"
        mock_together_api.assert_called_once()

class TestTools:
    async def test_website_generator_tool(self):
        """Test website generator tool"""
        tool = WebsiteGeneratorTool()
        result = await tool._arun(user_data=SAMPLE_WEBSITE_DATA)
        assert isinstance(result, str)
        assert "Generated website content" in result
        
    async def test_profile_optimizer_tool(self):
        """Test profile optimizer tool"""
        tool = ProfileOptimizerTool()
        result = await tool._arun(
            profile_data=SAMPLE_LINKEDIN_DATA,
            profile_type="linkedin"
        )
        assert isinstance(result, str)
        assert "Optimized linkedin profile" in result

# Integration Tests
class TestJobApplicationAgent:
    @pytest.mark.asyncio
    async def test_website_generation_flow(self, agent, mock_together_api):
        """Test complete website generation flow"""
        query = f"""
        I need help creating a personal website. Here's my information:
        {SAMPLE_WEBSITE_DATA}
        """
        response = await agent.process(query)
        assert isinstance(response, str)
        assert mock_together_api.called
        
    @pytest.mark.asyncio
    async def test_profile_optimization_flow(self, agent, mock_together_api):
        """Test complete profile optimization flow"""
        query = f"""
        Please optimize my LinkedIn profile:
        {SAMPLE_LINKEDIN_DATA}
        """
        response = await agent.process(query)
        assert isinstance(response, str)
        assert mock_together_api.called
        
    @pytest.mark.asyncio
    async def test_conversation_memory(self, agent, mock_together_api):
        """Test if agent maintains conversation context"""
        # First query
        await agent.process("Tell me about website generation")
        
        # Second query should have context from first
        response = await agent.process("Can you use my previous info for LinkedIn?")
        assert isinstance(response, str)
        assert len(agent.memory.chat_memory.messages) > 0

# Error handling tests
class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_invalid_api_key(self):
        """Test handling of invalid API key"""
        with pytest.raises(Exception):
            agent = JobApplicationAgent(api_key="invalid_key")
            await agent.process("Test query")
            
    @pytest.mark.asyncio
    async def test_invalid_input_format(self, agent):
        """Test handling of invalid input format"""
        query = "Invalid JSON format data"
        response = await agent.process(query)
        assert isinstance(response, str)
        assert "error" in response.lower() or "invalid" in response.lower()
