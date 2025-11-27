"""
Code executor for remote Python program execution.
WARNING: This uses exec() without sandboxing - for academic use only!
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CodeExecutor:
    """
    Executes Python code in a controlled environment.
    No sandboxing - executes code directly using exec().
    """
    
    def __init__(self):
        """Initialize the executor."""
        self.execution_count = 0
    
    def execute(self, task: Dict[str, Any]) -> Any:
        """
        Execute a CPU task.
        
        Args:
            task: Task dictionary with:
                - program: Python code string
                - function: Function name to call
                - args: List of arguments
        
        Returns:
            Result of function execution
        
        Raises:
            Exception: If execution fails
        """
        program = task.get("program", "")
        function_name = task.get("function", "main")
        args = task.get("args", [])
        
        if not program:
            raise ValueError("No program code provided")
        
        self.execution_count += 1
        logger.debug(f"Executing program (function: {function_name}, args: {args})")
        
        # Create a local execution environment
        local_env = {
            "__builtins__": __builtins__,
            "__name__": "__main__",
            "__file__": None,
        }
        
        try:
            # Execute the program code
            exec(program, local_env)
            
            # Get the function from the environment
            if function_name not in local_env:
                raise ValueError(f"Function '{function_name}' not found in program")
            
            func = local_env[function_name]
            
            if not callable(func):
                raise ValueError(f"'{function_name}' is not callable")
            
            # Call the function with provided arguments
            result = func(*args)
            
            logger.debug(f"Execution successful, result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get executor statistics."""
        return {
            "execution_count": self.execution_count
        }






