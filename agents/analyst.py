# agents/analyst.py
# It takes the research output
# Sends it to an LLM (Gemma 3)
# And asks the model to generate:
# -insights (bullets)
# -outline (sections for the report)
# -gaps (missing info)
# Then saves everything into:  outputs/analysis.json
# agents/analyst.py
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
            r.content = "Basic analysis completed."
            return r

MODEL = "llama3.2:1b"

class Analyst:
    def __init__(self, model_name: str = MODEL, client=None):
        self.client = client or (Ollama() if _OLLAMA_AVAILABLE else Ollama())
        self.model = model_name

    def run(self, research_data: dict) -> dict:
        logger.info("Starting analysis...")
        
        hits = research_data.get("hits", [])
        raw_research = research_data.get("raw", "")
        topic = research_data.get("topic", "Unknown")
        
        if not hits:
            logger.warning(" No data to analyze!")
            return {
                "insights": ["No data available for analysis"],
                "summary": "Analysis could not be completed due to lack of data."
            }
        
        # Simple prompt
        user_content = f"""Analyze this research on "{topic}":

{raw_research[:800]}

Provide:
1. Main themes (2-3 points)
2. Key insights (2-3 points)
3. Brief summary (1-2 sentences)"""

        try:
            logger.info(f"📤 Calling analyst model: {self.model}")
            resp = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a data analyst. Provide clear, structured insights."},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                options={"num_predict": 400}
            )
            
            analysis = getattr(resp, "content", "")
            logger.info(f" Analysis completed ({len(analysis)} chars)")
            
            if not analysis or len(analysis.strip()) < 20:
                analysis = self._generate_basic_analysis(hits, topic)
            
        except Exception as e:
            logger.error(f" Analysis failed: {e}")
            analysis = self._generate_basic_analysis(hits, topic)
        
        return {
            "insights": analysis.split('\n'),
            "summary": analysis,
            "source_count": len(hits)
        }
    
    def _generate_basic_analysis(self, hits, topic):
        """Fallback analysis"""
        analysis = f"Analysis of {topic}:\n\n"
        analysis += f"- Found {len(hits)} relevant sources\n"
        analysis += f"- Key source: {hits[0].get('title') if hits else 'N/A'}\n"
        analysis += f"- Further research recommended\n"
        return analysis