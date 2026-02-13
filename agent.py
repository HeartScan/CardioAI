import json
import requests
from typing import Dict, Any, List
from utils import get_config # Temporary, until we remove utils entirely
from llm_service import LLMService

class CardioAgent:
    """
    Agent responsible for orchestrating the flow: 
    1. Get raw data -> 2. Call HeartScan API for math -> 3. Call Dr7.ai for AI response.
    """
    def __init__(self, observation: Any):
        self.llm = LLMService()
        self.system_prompt = get_config("SYSTEM_PROMPT", section="DEFAULT")
        self.raw_observation = observation
        
        # External Math API Config
        self.math_api_url = "https://heartscan-api-175148683457.us-central1.run.app/api/v1/cardiolog/realtime_analysis"
        # X-API-Key should be in env
        from utils import get_secret
        self.math_api_key = get_secret("HEARTSCAN_API_KEY")

    def _get_math_analysis(self) -> Dict[str, Any]:
        """Calls the external HeartScan API to process raw accelerometer data."""
        if not self.math_api_key:
            print("Warning: HEARTSCAN_API_KEY not set. Math analysis might fail.")
            
        headers = {"X-API-Key": self.math_api_key}
        # In this specific case, the frontend sends exactly what the Math API needs
        response = requests.post(self.math_api_url, json=self.raw_observation, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise RuntimeError(f"Math API Error {response.status_code}: {response.text}")
            
        return response.json()

    def get_initial_response(self) -> str:
        """
        Generates the very first AI message by first getting math analysis.
        """
        try:
            obs_summary = self._get_math_analysis()
            
            self.history = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": f"Measurement Results: {json.dumps(obs_summary)}"}
            ]
            
            return self.llm.get_response(self.history)
        except Exception as e:
            print(f"Error in get_initial_response: {e}")
            return f"I'm sorry, I encountered an error while analyzing your data: {str(e)}"

    def handle_message(self, user_message: str, current_history: List[Dict[str, str]]) -> str:
        """
        Continues the dialogue. Note: we need the initial math context here too.
        In a stateless world, we assume current_history already contains the math summary from the first turn.
        """
        # If history is empty, it means we somehow lost context. 
        # In a real app, we'd fetch the math summary from a DB here.
        messages = current_history
        if not messages:
             # Fallback: re-run math if we have raw data but no history
             return self.get_initial_response()

        messages.append({"role": "user", "content": user_message})
        return self.llm.get_response(messages)
