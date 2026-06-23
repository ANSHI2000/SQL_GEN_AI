import os
import json
import re
import requests
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class HuggingFaceService:
    def __init__(self, schema_summary: str = None, api_key: str = None):
        self.schema_summary = schema_summary
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.model_id = "Qwen/Qwen2.5-7B-Instruct"
        self.base_url = "https://router.huggingface.co/v1/chat/completions"
    
    def generate_sql(self, natural_language_query: str) -> dict:
        """Generate SQL from natural language"""
        if not self.schema_summary:
            return {"error": "Schema summary is required", "options": []}
        if not self.api_key:
            return {"error": "HUGGINGFACE_API_KEY not configured", "options": []}
        
        prompt = f"""You are an expert SQL query generator. Given the following database schema and natural language query, generate 3 SQL query options.

Database Schema:
{self.schema_summary}

Natural Language Query: "{natural_language_query}"

Return ONLY a valid JSON object with this structure:
{{
    "options": [
        {{
            "sql": "SELECT ...",
            "confidence": 95,
            "explanation": "Why this query"
        }}
    ]
}}

Rules: Proper SQL syntax, JOINs, GROUP BY, ORDER BY, LIMIT. Return ONLY the JSON.
JSON:"""
        
        try:
            response_text = self._call_api(prompt, max_tokens=800, temperature=0.2)
            if not response_text:
                return {"error": "Empty response from API", "options": []}
            
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                return json.loads(json_match.group(0))
            
            return {"error": "Could not parse response", "options": []}
        except Exception as e:
            return {"error": str(e), "options": []}
    
    def explain_query(self, sql_query: str) -> str:
        """Explain SQL query"""
        if not self.schema_summary or not self.api_key:
            return "Schema or API key not configured"
        
        prompt = f"""Explain the following SQL query in simple language.
Database Schema: {self.schema_summary}
SQL Query: {sql_query}
Explanation:"""
        
        try:
            return self._call_api(prompt, max_tokens=400, temperature=0.5) or ""
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _call_api(self, prompt: str, max_tokens: int = 500, temperature: float = 0.3) -> str:
        """Call Hugging Face API"""
        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model_id,
                    "messages": [
                        {"role": "system", "content": "You are an expert SQL query generator. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": 0.9
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                raise Exception("Unexpected API response format")
            
            if response.status_code == 503:
                raise Exception("Hugging Face model is loading. Please wait 30 seconds and try again.")
            raise Exception(f"API error {response.status_code}: {response.text[:200]}")
            
        except requests.exceptions.Timeout:
            raise Exception("API request timed out after 10 seconds. Please try again later.")
        except requests.exceptions.ConnectionError:
            raise Exception("Cannot connect to Hugging Face API. Check your internet connection.")
        except Exception as e:
            raise Exception(f"API call failed: {str(e)}")
    
    def validate_sql(self, sql: str) -> dict:
        return {"valid": True, "sql": sql, "errors": [], "formatted_sql": sql}