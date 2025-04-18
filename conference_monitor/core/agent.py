"""
Base agent implementation for the Conference Monitor Agent
"""
from typing import Dict, List, Any, Optional
import logging
import requests
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from conference_monitor.config import (
    DEFAULT_LLM_MODEL, 
    DEFAULT_LLM_PROVIDER,
    OPENAI_API_KEY, 
    GOOGLE_API_KEY
)
from conference_monitor.core.memory import AgentMemory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_valid_google_api_key(api_key: str) -> bool:
    """Test if the Google API key is valid
    
    Args:
        api_key: Google API key to test
        
    Returns:
        True if the key is valid, False otherwise
    """
    if not api_key:
        return False
        
    # Skip validation if the key is a mock key for testing
    if api_key == "mock_google_api_key":
        return True
        
    # Test the API key with the generateContent endpoint (same as our test script)
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Test"
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            url=url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=5
        )
        
        # Check if the response is successful
        if response.status_code == 200:
            return True
        else:
            error_msg = response.json().get('error', {}).get('message', 'Unknown error')
            logger.warning(f"Google API key validation failed: {error_msg}")
            return False
    except Exception as e:
        logger.warning(f"Error validating Google API key: {str(e)}")
        return False

class ConferenceAgent:
    """Base agent for conference monitoring operations"""
    
    def __init__(self, 
                 model_name: str = DEFAULT_LLM_MODEL,
                 provider: str = DEFAULT_LLM_PROVIDER,
                 api_key: Optional[str] = None,
                 verbose: bool = False):
        """Initialize the conference agent
        
        Args:
            model_name: Name of the LLM model to use
            provider: LLM provider ('google' or 'openai')
            api_key: API key (uses one from config if not provided)
            verbose: Whether to log detailed information
        """
        self.verbose = verbose
        self.provider = provider
        
        # Set API key based on provider
        if provider == 'google':
            self.api_key = api_key or GOOGLE_API_KEY
            
            # Validate Google API key
            if not is_valid_google_api_key(self.api_key):
                raise ValueError("Invalid Google API key. Please provide a valid API key.")
        else:  # default to openai
            self.api_key = api_key or OPENAI_API_KEY
        
        # Check for API key
        if not self.api_key:
            raise ValueError(f"No {provider.capitalize()} API key found. Please provide a valid API key.")
        
        # Initialize LLM
        if self.provider == 'google':
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=0.2,
                    google_api_key=self.api_key,
                    verbose=verbose
                )
                logger.info(f"Using Google Gemini model: {model_name}")
            except Exception as e:
                logger.error(f"Error initializing Google Gemini model: {str(e)}")
                raise ValueError(f"Failed to initialize Google Gemini model: {str(e)}")
        else:
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=0.2,
                openai_api_key=self.api_key,
                verbose=verbose
            )
            logger.info(f"Using OpenAI model: {model_name}")
        
        # Initialize memory
        self.memory = AgentMemory()
        self.conversation_memory = ConversationBufferMemory(return_messages=True)
        
        if self.verbose:
            logger.info(f"Agent initialized with model: {model_name}")
    
    def run_query(self, query: str, system_prompt: str = "") -> str:
        """Run a simple query through the LLM
        
        Args:
            query: The query to process
            system_prompt: Optional system prompt to prepend
            
        Returns:
            The LLM's response as a string
        """
        try:
            prompt_template = f"{system_prompt}\n\n{{query}}" if system_prompt else "{query}"
            prompt = PromptTemplate(template=prompt_template, input_variables=["query"])
            chain = LLMChain(llm=self.llm, prompt=prompt)
            response = chain.run(query=query)
            return response
        except Exception as e:
            logger.error(f"Error running query: {str(e)}")
            return f"Error processing query: {str(e)}"
    
    def analyze_paper(self, paper_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a research paper and extract key information
        
        Args:
            paper_data: Dictionary containing paper metadata
            
        Returns:
            Dictionary with analysis results
        """
        title = paper_data.get("title", "")
        abstract = paper_data.get("abstract", "")
        
        if not title or not abstract:
            return {"error": "Paper data missing required fields (title, abstract)"}
        
        query = f"""
        Analyze the following research paper:
        
        Title: {title}
        Abstract: {abstract}
        
        Please provide:
        1. Key findings (3-5 bullet points)
        2. Main research contributions
        3. Research area/field
        4. Potential applications
        """
        
        analysis = self.run_query(query)
        
        return {
            "paper_id": paper_data.get("id", ""),
            "title": title,
            "analysis": analysis
        }
    
    def identify_trending_topics(self, papers: List[Dict[str, Any]]) -> List[str]:
        """Identify trending topics from a collection of papers
        
        Args:
            papers: List of paper data dictionaries
            
        Returns:
            List of trending topic strings
        """
        # Prepare paper data for LLM
        paper_info = []
        for i, paper in enumerate(papers[:20]):  # Limit to 20 papers for token constraints
            paper_info.append(f"{i+1}. {paper.get('title', 'Unknown')} - {paper.get('abstract', 'No abstract')[:200]}...")
        
        papers_text = "\n\n".join(paper_info)
        
        query = f"""
        Based on the following recent research papers, identify the top 5 trending topics or research directions.
        For each trend, provide a brief explanation of why it's significant.
        
        Papers:
        {papers_text}
        """
        
        response = self.run_query(query)
        
        # Process response
        trends = []
        if response and ":" in response:
            for line in response.split("\n"):
                line = line.strip()
                if line and (line.startswith(("- ", "• ", "* ")) or
                             (line[0].isdigit() and line[1:].startswith((". ", ") ")))):
                    trends.append(line)
        
        return trends or ["No clear trends identified"] 