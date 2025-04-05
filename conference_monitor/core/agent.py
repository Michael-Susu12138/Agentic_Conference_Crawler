"""
Base agent implementation for the Conference Monitor Agent
"""
from typing import Dict, List, Any, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from conference_monitor.config import DEFAULT_LLM_MODEL, OPENAI_API_KEY
from conference_monitor.core.memory import AgentMemory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConferenceAgent:
    """Base agent for conference monitoring operations"""
    
    def __init__(self, 
                 model_name: str = DEFAULT_LLM_MODEL,
                 api_key: Optional[str] = None,
                 verbose: bool = False,
                 mock_mode: bool = False):
        """Initialize the conference agent
        
        Args:
            model_name: Name of the OpenAI model to use
            api_key: OpenAI API key (uses one from config if not provided)
            verbose: Whether to log detailed information
            mock_mode: If True, use mock responses instead of API calls
        """
        self.verbose = verbose
        self.api_key = api_key or OPENAI_API_KEY
        self.mock_mode = mock_mode
        
        # Check for API key if not in mock mode
        if not self.mock_mode and not self.api_key:
            logger.warning("OpenAI API key not found. Running in mock mode.")
            self.mock_mode = True
        
        # Initialize LLM if not in mock mode
        if not self.mock_mode:
            self.llm = ChatOpenAI(
                model=model_name,
                temperature=0.2,
                openai_api_key=self.api_key,
                verbose=verbose
            )
        else:
            self.llm = None
            logger.info("Running in mock mode - no API calls will be made")
        
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
        if self.mock_mode:
            # Return a mock response instead of calling the API
            logger.info(f"Mock mode: Query received: {query[:50]}...")
            return "This is a mock response since no API key is available."
        
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
        
        if self.mock_mode:
            # Return mock analysis
            return {
                "paper_id": paper_data.get("id", ""),
                "title": title,
                "analysis": "Mock analysis: This paper presents interesting findings in the field."
            }
        
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
        if self.mock_mode:
            # Return mock trending topics
            return [
                "1. Machine Learning for Healthcare",
                "2. Transformer Models for NLP",
                "3. Reinforcement Learning Advancements",
                "4. Computer Vision Applications",
                "5. Ethical AI and Fairness"
            ]
        
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
        for line in response.split("\n"):
            line = line.strip()
            if line and (line.startswith("-") or line.startswith("•") or any(str(i) in line[:3] for i in range(1, 6))):
                trends.append(line)
        
        return trends 