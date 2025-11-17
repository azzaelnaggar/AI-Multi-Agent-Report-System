# agents/writer.py (With Feedback Support)
from utils.prompts import WRITER_PROMPT
from tools.file_tool import save_text, save_json
from datetime import date
import json
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
            r.content = ""
            return r

MODEL = "gemma3:latest"

class Writer:
    def __init__(self, model_name: str = MODEL, client=None, author: str = "AutoAgent"):
        self.client = client or (Ollama() if _OLLAMA_AVAILABLE else Ollama())
        self.model = model_name
        self.author = author

    def run(self, analysis_struct: dict, title: str = None):
        logger.info(" Starting report writing...")
        
        title = title or analysis_struct.get("topic") or "Automated Report"
        today = date.today().isoformat()
        
        hits = analysis_struct.get("hits", [])
        analysis_text = analysis_struct.get("analysis", analysis_struct.get("raw", ""))
        previous_feedback = analysis_struct.get("previous_feedback", "")
        
        logger.info(f" Writing report with {len(hits)} sources")
        
        if not hits:
            logger.warning(" No research hits available!")
            return self._generate_minimal_report(title, today)
        
        # Build user content
        user_content = f"""Write a professional report about: {title}

Author: {self.author}
Date: {today}

Research Summary:
{analysis_text[:1000]}

Sources:
"""
        for i, h in enumerate(hits[:5], 1):
            user_content += f"{i}. {h.get('title')} - {h.get('url')}\n"
        
        # Add feedback if this is a rewrite
        if previous_feedback:
            user_content += f"""

IMPORTANT - Previous version had issues. Please improve based on this feedback:
{previous_feedback}

Make sure to address all the points mentioned above.
"""
            logger.info("Including previous feedback in prompt")
        
        user_content += """

Write a markdown report with:
1. Introduction (2-3 sentences)
2. Main Findings (bullet points)
3. Detailed Analysis
4. Conclusion (2-3 sentences)
5. References

Keep it professional, well-structured, and comprehensive."""

        logger.info(f" Calling model: {self.model}")
        
        try:
            resp = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": WRITER_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.5 if not previous_feedback else 0.7,  # More creative on retry
                options={
                    "num_predict": 1500 if previous_feedback else 1000,  # Longer on retry
                }
            )
            
            md = getattr(resp, "content", "")
            logger.info(f" Model response received ({len(md)} chars)")
            
            # Validate response
            if not md or len(md.strip()) < 50:
                logger.warning(" Model response too short, using fallback")
                md = self._generate_structured_report(title, today, hits, analysis_text)
            
        except Exception as e:
            logger.error(f" Model call failed: {e}")
            md = self._generate_structured_report(title, today, hits, analysis_text)
        
        # Save outputs
        save_text(md, "report.md")
        logger.info(" Report saved to report.md")
        
        return md
    
    def _generate_structured_report(self, title, date, hits, analysis):
        """Generate a proper structured report as fallback"""
        md = f"# {title}\n\n"
        md += f"**Author:** {self.author}  \n"
        md += f"**Date:** {date}  \n\n"
        md += "---\n\n"
        
        md += "## Introduction\n\n"
        md += f"This report presents comprehensive research findings on {title}. "
        md += f"The analysis is based on {len(hits)} authoritative sources from various publications. "
        md += "This document aims to provide a thorough understanding of the subject matter.\n\n"
        
        md += "## Key Findings\n\n"
        if analysis:
            lines = analysis.split('\n')
            for line in lines[:10]:
                if line.strip() and len(line.strip()) > 20:
                    md += f"- {line.strip()}\n"
        else:
            for h in hits[:5]:
                snippet = h.get('snippet', '')[:200]
                md += f"- **{h.get('title')}**: {snippet}...\n"
        
        md += "\n## Detailed Analysis\n\n"
        md += f"The research on {title} reveals several important aspects:\n\n"
        
        for i, h in enumerate(hits[:3], 1):
            md += f"### {i}. {h.get('title')}\n\n"
            md += f"{h.get('snippet', 'No description available')}...\n\n"
            md += f"*Source: [{h.get('url')}]({h.get('url')})*\n\n"
        
        md += "## Conclusion\n\n"
        md += f"Based on the comprehensive research conducted, {title} demonstrates significant relevance "
        md += "in current discussions and developments. The findings suggest that further investigation "
        md += "and continued monitoring of this topic would be beneficial. "
        md += "This report provides a solid foundation for understanding the key aspects and implications.\n\n"
        
        md += "## References\n\n"
        for i, h in enumerate(hits, 1):
            md += f"{i}. [{h.get('title')}]({h.get('url')})\n"
        
        return md
    
    def _generate_minimal_report(self, title, date):
        """Minimal report when no data available"""
        md = f"# {title}\n\n"
        md += f"**Author:** {self.author}  \n"
        md += f"**Date:** {date}  \n\n"
        md += "---\n\n"
        md += "## Note\n\n"
        md += "No research data was available for this report.\n"
        return md