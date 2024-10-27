import pytest
from unittest.mock import patch
from langchain_agents.agent import JobApplicationAgent
from langchain_agents.tools import WebsiteGeneratorTool, ProfileOptimizerTool
from langchain_agents.custom_together_llm import TogetherLLM

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
            'choices': [{
                'text': 'Mocked response from Together AI'
            }]
        }
        yield mock_create

@pytest.fixture
async def agent():
    """Create a test agent instance"""
    return JobApplicationAgent()

# Unit Tests
class TestTogetherLLM:
    @pytest.mark.asyncio
    async def test_llm_call(self, mock_together_api):
        """Test LLM call functionality"""
        llm = TogetherLLM()
        response = llm._call("Test prompt")
        assert isinstance(response, str)
        assert mock_together_api.called

class TestTools:
    @pytest.mark.asyncio
    async def test_website_generator_tool(self):
        """Test website generator tool"""
        tool = WebsiteGeneratorTool()
        result = tool._run(
            name=SAMPLE_WEBSITE_DATA["name"],
            experience=SAMPLE_WEBSITE_DATA["experience"],
            skills=SAMPLE_WEBSITE_DATA["skills"]
        )
        assert isinstance(result, str)
        assert SAMPLE_WEBSITE_DATA["name"] in result
        assert any(exp in result for exp in SAMPLE_WEBSITE_DATA["experience"])
        assert any(skill in result for skill in SAMPLE_WEBSITE_DATA["skills"])
        
    @pytest.mark.asyncio
    async def test_profile_optimizer_tool(self):
        """Test profile optimizer tool"""
        tool = ProfileOptimizerTool()
        result = tool._run(
            url="https://linkedin.com/in/johndoe",
            profile_type="linkedin"
        )
        assert isinstance(result, str)
        assert "Profile Optimization Tips for linkedin" in result
        assert "professional profile" in result.lower()

    @pytest.mark.asyncio
    async def test_profile_optimizer_invalid_type(self):
        """Test profile optimizer with invalid profile type"""
        tool = ProfileOptimizerTool()
        result = tool._run(
            url="https://example.com",
            profile_type="invalid"
        )
        assert "Error: Profile type must be either 'LinkedIn' or 'GitHub'" in result

# Integration Tests
class TestJobApplicationAgent:
    @pytest.mark.asyncio
    async def test_website_generation_flow(self, agent, mock_together_api):
        """Test complete website generation flow"""
        query = f"""
        I need help creating a personal website. Here's my information:
        {SAMPLE_WEBSITE_DATA}
        """
        # Properly await the agent fixture
        response = await (await agent).process(query)
        assert isinstance(response, str)
        assert mock_together_api.called
        
    @pytest.mark.asyncio
    async def test_profile_optimization_flow(self, agent, mock_together_api):
        """Test complete profile optimization flow"""
        query = f"""
        Please optimize my LinkedIn profile:
        {SAMPLE_LINKEDIN_DATA}
        """
        # Properly await the agent fixture
        response = await (await agent).process(query)
        assert isinstance(response, str)
        assert mock_together_api.called
        
    @pytest.mark.asyncio
    async def test_conversation_memory(self, agent, mock_together_api):
        """Test if agent maintains conversation context"""
        # Properly await the agent fixture
        agent_instance = await agent
        
        # First query
        await agent_instance.process("Tell me about website generation")
        
        # Second query should have context from first
        response = await agent_instance.process("Can you use my previous info for LinkedIn?")
        assert isinstance(response, str)
        assert len(agent_instance.memory.chat_memory.messages) > 0
