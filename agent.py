import json
from typing import Dict, Any, List
from utils import get_config, preprocess_obs
from llm_service import LLMService

class CardioAgent:
    """
    Agent responsible for handling medical chat logic and maintaining dialogue context.
    """
    def __init__(self, observation: Any):
        self.llm = LLMService()
        self.system_prompt = get_config("SYSTEM_PROMPT", section="DEFAULT")
        self.observation = observation
        
        # Initial context: system prompt + measurement data
        obs_summary = preprocess_obs(observation)
        self.history = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Measurement Results: {json.dumps(obs_summary)}"}
        ]

    def get_initial_response(self) -> str:
        """
        Generates the very first AI message based on measurement data.
        """
        return self.llm.get_response(self.history)

    def handle_message(self, user_message: str, current_history: List[Dict[str, str]]) -> str:
        """
        Processes a user message given the current history and returns the AI response.
        """
        # Ensure we always have the initial context
        messages = self.history + current_history
        messages.append({"role": "user", "content": user_message})
        
        response = self.llm.get_response(messages)
        return response
