# agents/researcher.py
# Search the web for a topic
# Prepare the search results
# Send them to an LLM model (like Ollama)
# Get the model’s analysis
# Save everything to a JSON file

from tools.search_tool import search_web
from utils.prompts import RESEARCH_PROMPT
from tools.file_tool import save_json
from typing import Dict
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama client fallback wrapper
try:
    from ollama import Ollama
    _OLLAMA_AVAILABLE = True
except Exception:
    _OLLAMA_AVAILABLE = False
    class Ollama:
        def __init__(self, *a, **k): pass
        def chat(self, *a, **k):
            class R: pass
            r = R()
            r.content = "[]"
            return r

MODEL = "llama3.2:1b"

class Researcher:
    def __init__(self, model_name: str = MODEL, client=None):
        self.client = client or (Ollama() if _OLLAMA_AVAILABLE else Ollama())
        self.model = model_name

    def run(self, topic: str, top_k: int = 5) -> Dict:
        logger.info(f"🔍 Starting research for topic: {topic}")
        
        # Get search results
        hits = search_web(topic, max_results=top_k)
        logger.info(f" Found {len(hits)} search results")
        
        if not hits:
            logger.warning(" No search results found!")
            return {
                "topic": topic,
                "timestamp": datetime.utcnow().isoformat(),
                "hits": [],
                "raw": "[]",
                "analysis": "No results found"
            }
        
        # Prepare SIMPLE prompt for the model
        user_content = f"""Analyze these search results about "{topic}":

"""
        for i, h in enumerate(hits, 1):
            user_content += f"{i}. {h.get('title')}\n"
            user_content += f"   URL: {h.get('url')}\n"
            snippet = h.get('snippet', '')[:200]  # Limit snippet length
            user_content += f"   Info: {snippet}\n\n"
        
        user_content += "\nProvide 3-5 key insights about this topic in simple bullet points."
        
        logger.info(f" Sending prompt to model: {self.model}")
        
        try:
            # Call Ollama
            resp = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research analyst. Provide clear, concise insights."},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                options={
                    "num_predict": 500,  # Limit response length
                }
            )
            
            raw = getattr(resp, "content", str(resp))
            logger.info(f" Model response received ({len(raw)} chars)")
            logger.debug(f"Raw response: {raw[:200]}...")
            
            # Validate response
            if not raw or raw.strip() in ["", "[]", "{}"]:
                logger.warning(" Model returned empty response, using fallback")
                raw = self._generate_fallback_analysis(hits, topic)
            
        except Exception as e:
            logger.error(f"Model call failed: {e}")
            raw = self._generate_fallback_analysis(hits, topic)
        
        out = {
            "topic": topic,
            "timestamp": datetime.utcnow().isoformat(),
            "hits": hits,
            "raw": raw,
            "analysis": raw  # Add analysis field
        }
        
        # Save to file
        save_json(out, f"research_{topic.replace(' ','_')}")
        logger.info(" Research saved to JSON")
        
        return out
    
    def _generate_fallback_analysis(self, hits, topic):
        """Generate basic analysis when model fails"""
        analysis = f"Analysis of '{topic}':\n\n"
        analysis += f"Found {len(hits)} relevant sources:\n\n"
        for i, h in enumerate(hits[:3], 1):
            analysis += f"{i}. {h.get('title')}\n"
            analysis += f"   Source: {h.get('url')}\n\n"
        return analysis