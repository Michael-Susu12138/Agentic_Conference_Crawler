"""
Base tool class for conference monitor agent tools
"""
from typing import Dict, List, Any, Optional, Callable
import logging
from abc import ABC, abstractmethod

# Set up logging
logger = logging.getLogger(__name__)

class BaseTool(ABC):
    """Base class for all agent tools"""
    
    def __init__(self, name: str, description: str):
        """Initialize a base tool
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
        """
        self.name = name
        self.description = description
        self._pre_hooks: List[Callable] = []
        self._post_hooks: List[Callable] = []
    
    def add_pre_hook(self, hook: Callable):
        """Add a hook to run before tool execution
        
        Args:
            hook: Function to run before tool execution
        """
        self._pre_hooks.append(hook)
    
    def add_post_hook(self, hook: Callable):
        """Add a hook to run after tool execution
        
        Args:
            hook: Function to run after tool execution
        """
        self._post_hooks.append(hook)
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with the given parameters
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dictionary with the tool's results and any additional metadata
        """
        # Run pre-hooks
        for hook in self._pre_hooks:
            try:
                hook(self, **kwargs)
            except Exception as e:
                logger.error(f"Error in pre-hook for tool {self.name}: {str(e)}")
        
        try:
            # Run the actual tool implementation
            start_time = logger.isEnabledFor(logging.DEBUG)
            
            logger.info(f"Executing tool: {self.name}")
            result = self._execute(**kwargs)
            
            # Add metadata to result
            if not isinstance(result, dict):
                result = {"result": result}
            
            result["tool_name"] = self.name
            
            return result
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {str(e)}")
            return {
                "tool_name": self.name,
                "error": str(e),
                "success": False
            }
        finally:
            # Run post-hooks
            for hook in self._post_hooks:
                try:
                    hook(self, result=result, **kwargs)
                except Exception as e:
                    logger.error(f"Error in post-hook for tool {self.name}: {str(e)}")
    
    @abstractmethod
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Tool-specific implementation
        
        Args:
            **kwargs: Tool-specific parameters
            
        Returns:
            Dictionary with the tool's results
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the tool's schema for use with LLM agents
        
        Returns:
            Dictionary representing the tool's schema
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self._get_parameters_schema()
            }
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """Get the schema for the tool's parameters
        
        Returns:
            Dictionary representing the tool's parameters schema
        """
        pass 