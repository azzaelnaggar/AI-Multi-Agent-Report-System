# main.py 
import logging
from agents.researcher import Researcher
from agents.analyst import Analyst
from agents.writer import Writer
from agents.critic import Critic
from tools.file_tool import save_text
import markdown
import os

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('outputs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_pipeline(topic: str, title: str = None, author: str = "AutoAgent", max_retries: int = 2):
    """
    Main pipeline with feedback loop.
    
    Args:
        topic: Research topic
        title: Optional custom report title
        author: Report author name
        max_retries: Maximum number of rewrites if score is low
        
    Returns:
        Dictionary with pipeline results
    """
    logger.info(f"Pipeline started for topic: {topic}")
    
    try:
        # 1. Research Phase
        logger.info("=" * 50)
        logger.info("PHASE 1: RESEARCH")
        logger.info("=" * 50)
        researcher = Researcher()
        research_data = researcher.run(topic)
        
        hits_count = len(research_data.get("hits", []))
        logger.info(f"Found {hits_count} search results")
        
        if hits_count == 0:
            logger.error("No search results found")
            raise Exception("No search results found")
        
        # 2. Analysis Phase
        logger.info("=" * 50)
        logger.info("PHASE 2: ANALYSIS")
        logger.info("=" * 50)
        analyst = Analyst()
        analysis = analyst.run(research_data)
        logger.info("Analysis completed")
        
        # 3. Writing Phase (with potential retries)
        logger.info("=" * 50)
        logger.info("PHASE 3: WRITING")
        logger.info("=" * 50)
        writer = Writer(author=author)
        critic = Critic()
        
        full_data = {**research_data, "analysis": analysis.get("summary", "")}
        
        markdown_text = None
        critique_result = None
        attempt = 0
        
        while attempt <= max_retries:
            attempt += 1
            logger.info(f"Writing attempt {attempt}/{max_retries + 1}...")
            
            # Write report
            if attempt == 1:
                # First attempt - normal write
                markdown_text = writer.run(full_data, title=title)
            else:
                # Retry with feedback from previous critique
                logger.info(f"Rewriting with feedback: {critique_result.get('feedback', '')[:100]}...")
                # Add feedback to the data
                full_data["previous_feedback"] = critique_result.get('feedback', '')
                markdown_text = writer.run(full_data, title=title)
            
            if not markdown_text or len(markdown_text) < 100:
                logger.warning("Writer produced minimal content")
                if attempt > max_retries:
                    break
                continue
            
            logger.info(f"Report generated ({len(markdown_text)} chars)")
            
            # 4. Critique Phase
            logger.info("=" * 50)
            logger.info(f"PHASE 4: CRITIQUE (Attempt {attempt})")
            logger.info("=" * 50)
            
            critique_result = critic.run(markdown_text)
            
            score = critique_result.get('score', 0)
            passed = critique_result.get('passed', False)
            feedback = critique_result.get('feedback', '')
            
            logger.info(f"Score: {score}/100")
            logger.info(f"Feedback: {feedback[:150]}...")
            
            if passed:
                logger.info("Report passed quality check")
                break
            else:
                logger.warning(f"Score too low ({score} < {critic.get_threshold()})")
                if attempt <= max_retries:
                    logger.info("Retrying with improvements...")
                else:
                    logger.warning("Max retries reached, using last version")
        
        # 5. Export Phase
        logger.info("=" * 50)
        logger.info("PHASE 5: EXPORT")
        logger.info("=" * 50)
        
        # Simple HTML export without inline CSS
        html_content = f"""
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or topic}</title>
</head>
<body>
    <h1>{title or topic}</h1>
    <p>Author: {author}</p>
    <p>Score: {critique_result.get('score', 0)}/100</p>
    <div>
        {markdown.markdown(markdown_text, extensions=['extra', 'codehilite'])}
    </div>
</body>
</html>
"""
        
        html_path = "outputs/final_report.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        md_path = "outputs/final_report.md"
        save_text(markdown_text, "final_report.md")
        
        logger.info("=" * 50)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"HTML Report: {html_path}")
        logger.info(f"Markdown: {md_path}")
        logger.info(f"Final Score: {critique_result.get('score', 0)}/100")
        logger.info(f"Attempts: {attempt}")
        
        return {
            "success": True,
            "research_path": f"outputs/research_{topic.replace(' ','_')}.json",
            "final_md_path": md_path,
            "pdf_path": html_path,
            "score": critique_result.get('score', 0),
            "passed": critique_result.get('passed', False),
            "feedback": critique_result.get('feedback', ''),
            "hits_count": hits_count,
            "attempts": attempt
        }
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # Test run
    result = run_pipeline(
        topic="Artificial Intelligence",
        title="AI Report",
        author="Auto Report System",
        max_retries=2  # Will retry up to 2 times if quality is low
    )
    
    if result["success"]:
        print("\n" + "=" * 60)
        print("PIPELINE COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print(f"Report: {result['pdf_path']}")
        print(f"Score: {result['score']}/100")
        print(f"Quality: {'PASSED' if result['passed'] else 'ACCEPTABLE'}")
        print(f"Attempts: {result['attempts']}")
        if result.get('feedback'):
            print(f"Feedback: {result['feedback'][:100]}...")
    else:
        print(f"\nPipeline failed: {result['error']}")
