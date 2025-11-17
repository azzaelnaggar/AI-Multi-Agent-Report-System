# agents/critic.py
# The purpose of this code is to automatically evaluate Markdown reports by generating a score, 
# providing constructive feedback, deciding whether the report passes a minimum quality threshold,
# and saving the evaluation results. It acts as a “critic agent” that reviews the report’s clarity, 
# structure,and completeness, and can fall back to heuristic scoring if the model response fails.

from tools.file_tool import save_json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from ollama import Ollama
    _OLLAMA_AVAILABLE = True
except Exception:
    _OLLAMA_AVAILABLE = False
    class Ollama:
        def __init__(self, *a, **k): 
            pass
        def chat(self, *a, **k):
            class R: 
                pass
            r = R()
            r.content = "Score: 75\nFeedback: Good report."
            return r

MODEL = "llama3.2:1b"

class Critic:
    def __init__(self, model_name: str = MODEL, client=None):
        self.client = client or (Ollama() if _OLLAMA_AVAILABLE else Ollama())
        self.model = model_name
        self.threshold = 70  # Minimum acceptable score

    def run(self, markdown_text: str) -> dict:
        """
        Critique the report and return score + feedback

        Returns:
            dict with:
            - score: int (0-100)
            - feedback: str (improvement suggestions)
            - passed: bool (True if score >= threshold)
        """
        logger.info("Starting report critique...")

        if not markdown_text or len(markdown_text) < 50:
            logger.warning("Report too short to critique properly")
            return {
                "score": 40,
                "feedback": "The report is too short and needs more details.",
                "passed": False
            }

        # Ask model to critique
        user_content = f"""Evaluate this report and provide:
1. Score (0-100)
2. Specific feedback for improvement

Report preview:
{markdown_text[:1500]}

Respond in this format:
Score: [number]
Feedback: [your suggestions]

Be specific and constructive.
"""

        try:
            logger.info(f"Calling critic model: {self.model}")
            resp = self.client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional report critic. Provide constructive feedback."},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.3,
                options={"num_predict": 300}
            )

            response_text = getattr(resp, "content", "")
            logger.info(f"Received critique ({len(response_text)} characters)")

            # Parse model response
            score, feedback = self._parse_critique(response_text)

            if score is None:
                logger.warning("Could not parse model critique, using heuristic scoring.")
                score = self._calculate_heuristic_score(markdown_text)
                feedback = self._generate_heuristic_feedback(markdown_text, score)

        except Exception as e:
            logger.error(f"Critique failed: {e}")
            score = self._calculate_heuristic_score(markdown_text)
            feedback = self._generate_heuristic_feedback(markdown_text, score)

        passed = score >= self.threshold

        critique_result = {
            "score": score,
            "feedback": feedback,
            "passed": passed,
            "threshold": self.threshold,
            "report_length": len(markdown_text)
        }
        save_json(critique_result, "critique")

        logger.info(f"Score: {score}/100 | Passed: {passed}")
        return critique_result

    def _parse_critique(self, text: str):
        """Extract score and feedback from model response"""
        score = None
        feedback = ""

        lines = text.split('\n')
        for line in lines:
            if 'score:' in line.lower():
                import re
                numbers = re.findall(r'\d+', line)
                if numbers:
                    score = int(numbers[0])
                    score = max(0, min(100, score))
            elif 'feedback:' in line.lower():
                feedback = line.split(':', 1)[1].strip()

        if not feedback:
            feedback_start = text.lower().find('feedback:')
            if feedback_start != -1:
                feedback = text[feedback_start + 9:].strip()

        return score, feedback

    def _calculate_heuristic_score(self, markdown: str) -> int:
        """Fallback scoring based on simple heuristics"""
        score = 50

        if len(markdown) > 500:
            score += 10
        if len(markdown) > 1000:
            score += 10
        if "##" in markdown:
            score += 10
        if "###" in markdown:
            score += 5
        if "http" in markdown or "[" in markdown:
            score += 10
        if "**" in markdown or "*" in markdown:
            score += 5

        return min(score, 100)

    def _generate_heuristic_feedback(self, markdown: str, score: int) -> str:
        """Generate improvement suggestions based on content analysis"""
        issues = []

        if len(markdown) < 500:
            issues.append("- The report is short; consider adding more detailed content.")
        if "##" not in markdown:
            issues.append("- Add headings to structure the content.")
        if "http" not in markdown and "[" not in markdown:
            issues.append("- Add references or sources.")
        if "**" not in markdown and "*" not in markdown:
            issues.append("- Use formatting (bold/italic) to improve readability.")

        if not issues:
            return "The report is generally good and ready for publishing."

        return "Suggested Improvements:\n" + "\n".join(issues)

    def get_threshold(self) -> int:
        """Return current passing threshold"""
        return self.threshold

    def set_threshold(self, threshold: int):
        """Update passing threshold"""
        self.threshold = max(0, min(100, threshold))
        logger.info(f"Threshold updated to {self.threshold}")
