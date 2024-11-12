import json
from pathlib import Path
import asyncio
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv
import argparse
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_conversation(data):
    """Analyze the conversation flow and effectiveness"""
    try:
        prompt = f"""
        Analyze this sales conversation between a Company representative and a Customer. The conversation includes sentiment analysis for each utterance.
        
        Focus on:
        1. Key Moments:
           - Identify pivotal moments where customer sentiment changed
           - Note which company statements led to positive customer reactions
           - Highlight any missed opportunities or points of confusion

        2. Conversation Flow:
           - Evaluate the opening approach
           - Assess how well objections were handled
           - Analyze the closing effectiveness

        3. Customer Engagement:
           - Track customer sentiment progression
           - Identify topics that resonated most
           - Note any signs of hesitation or concern

        4. Recommendations:
           - Suggest alternative approaches where applicable
           - Identify best practices demonstrated
           - Provide specific improvement opportunities

        Conversation Data:
        {json.dumps(data, indent=2)}

        Provide analysis in the following JSON structure:
        {{
            "key_moments": [
                {{
                    "moment": str,  # Description of the key moment
                    "utterance_index": int,  # Index in the conversation
                    "impact": str,  # Positive/Negative/Neutral impact
                    "explanation": str  # Why this moment was significant
                }}
            ],
            "conversation_flow": {{
                "opening_effectiveness": str,
                "objection_handling": str,
                "closing_effectiveness": str,
                "overall_flow_rating": float  # 0.0 to 1.0
            }},
            "customer_engagement": {{
                "sentiment_progression": str,
                "resonating_topics": [str],
                "concern_points": [str]
            }},
            "recommendations": {{
                "strengths": [str],
                "improvement_areas": [str],
                "best_practices": [str]
            }},
            "overall_effectiveness_score": float  # 0.0 to 1.0
        }}
        """

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert sales conversation analyst focusing on effectiveness and customer engagement."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Error analyzing conversation: {str(e)}")
        return None

async def process_file(file_path: Path):
    """Process a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis = await analyze_conversation(data)
        if analysis:
            # Combine original data with analysis
            data['conversation_analysis'] = analysis
            return data
        return None

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

async def main(input_file=None):
    try:
        source_dir = Path('/Users/azadneenan/Documents/clipboard_health/trasncriptions_with_sentiment')
        target_dir = Path('/Users/azadneenan/Documents/clipboard_health/transcription_summary')
        target_dir.mkdir(exist_ok=True)

        if input_file:
            input_path = Path(input_file)
            logger.info(f"Processing: {input_path.name}")
            processed_data = await process_file(input_path)
            if processed_data:
                output_path = target_dir / input_path.name
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Analysis saved: {output_path}")
        else:
            for json_file in source_dir.glob('*.json'):
                logger.info(f"Processing: {json_file.name}")
                processed_data = await process_file(json_file)
                if processed_data:
                    output_path = target_dir / json_file.name
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(processed_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Analysis saved: {output_path}")

    except Exception as e:
        logger.critical(f"Error during conversation analysis: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze sales conversation effectiveness')
    parser.add_argument('--file', type=str, help='Path to specific JSON file to process')
    args = parser.parse_args()
    
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args.file)) 