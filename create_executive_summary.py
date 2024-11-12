import json
from pathlib import Path
import asyncio
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def create_executive_summary(files_data):
    """Create a high-level executive summary of all conversations"""
    try:
        prompt = f"""
        Create a high-level executive summary of these sales conversations. Focus on identifying patterns 
        and themes across all conversations, not individual details.

        Conversation Analyses:
        {json.dumps(files_data, indent=2)}

        Create an executive summary that focuses on:
        1. Key Themes - What patterns emerged across conversations?
        2. Customer Sentiment - Where was sentiment consistently positive or negative?
        3. Improvement Areas - What high-level changes would improve overall sales effectiveness?

        Provide the analysis in the following JSON structure:
        {{
            "key_themes": [
                {{
                    "theme": str,
                    "pattern": str,
                    "significance": str
                }}
            ],
            "sentiment_analysis": {{
                "positive_areas": [
                    {{
                        "area": str,
                        "impact": str
                    }}
                ],
                "negative_areas": [
                    {{
                        "area": str,
                        "improvement_opportunity": str
                    }}
                ]
            }},
            "strategic_recommendations": [
                {{
                    "recommendation": str,
                    "expected_outcome": str
                }}
            ],
            "executive_summary": str  # 2-3 paragraphs summarizing the key findings
        }}
        """

        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert sales strategist creating a high-level executive summary of sales conversations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Error creating executive summary: {str(e)}")
        return None

async def main():
    try:
        source_dir = Path('/Users/azadneenan/Documents/clipboard_health/final_analysis')
        target_dir = Path('/Users/azadneenan/Documents/clipboard_health/consolidated_analysis')
        target_dir.mkdir(exist_ok=True)

        # Read all JSON files
        files_data = []
        for json_file in source_dir.glob('*.json'):
            logger.info(f"Reading: {json_file.name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                files_data.append(json.load(f))

        if not files_data:
            logger.warning("No files found to analyze")
            return

        # Create executive summary
        logger.info("Creating executive summary...")
        summary = await create_executive_summary(files_data)

        if summary:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Create markdown summary
            summary_path = target_dir / f"executive_summary_{timestamp}.md"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("# Sales Conversations Executive Summary\n\n")
                f.write(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Conversations Analyzed: {len(files_data)}\n\n")
                
                # Executive Summary
                f.write("## Executive Summary\n\n")
                f.write(summary['executive_summary'])
                f.write("\n\n")
                
                # Key Themes
                f.write("## Key Themes\n\n")
                for theme in summary['key_themes']:
                    f.write(f"### {theme['theme']}\n")
                    f.write(f"**Pattern:** {theme['pattern']}\n")
                    f.write(f"**Significance:** {theme['significance']}\n\n")
                
                # Sentiment Analysis
                f.write("## Customer Sentiment Analysis\n\n")
                
                f.write("### Areas of Positive Reception\n")
                for area in summary['sentiment_analysis']['positive_areas']:
                    f.write(f"- **{area['area']}**\n")
                    f.write(f"  - Impact: {area['impact']}\n\n")
                
                f.write("### Areas Needing Improvement\n")
                for area in summary['sentiment_analysis']['negative_areas']:
                    f.write(f"- **{area['area']}**\n")
                    f.write(f"  - Opportunity: {area['improvement_opportunity']}\n\n")
                
                # Strategic Recommendations
                f.write("## Strategic Recommendations\n\n")
                for rec in summary['strategic_recommendations']:
                    f.write(f"- **{rec['recommendation']}**\n")
                    f.write(f"  - Expected Outcome: {rec['expected_outcome']}\n\n")

            logger.info(f"Executive summary saved: {summary_path}")

            # Save raw JSON data
            json_path = target_dir / f"executive_summary_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "meta": {
                        "analysis_date": datetime.now().isoformat(),
                        "conversations_analyzed": len(files_data)
                    },
                    "summary": summary
                }, f, indent=2, ensure_ascii=False)

            logger.info(f"JSON data saved: {json_path}")

    except Exception as e:
        logger.critical(f"Error during executive summary creation: {str(e)}")

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main()) 