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

# Define product pitches
PRODUCT_PITCHES = {
    "Smooth Revenue": """
    Appeals to people worried about spikiness in reservations. Soft Skillet helps restaurants have more certainty about revenue. 
    Rather than hoping that restaurants will book out, Soft Skillet takes in data and provides a guarantee that there will be 
    at least X guests on a given day. If Soft Skillet makes a bad prediction they'll pay restaurants, which helps restaurants 
    better budget food costs.
    """,
    
    "AI Seating": """
    Appeals to people who see themselves as innovators. Soft Skillet uses AI to optimize seating arrangements in restaurants 
    to deliver more revenue. Rather than seeing a bunch of large parties book on Friday and Saturdays and small parties book 
    on other days of the week, Soft Skillet uses AI to drive mixes that help restaurants grow their topline through mix in 
    table type. Rather than allowing a bunch of two tops to be booked on Thursday night Soft Skillet will hold reservations 
    for a longer time when the probability of filling a larger party is higher (with higher order volume), especially when 
    walk in demand is high so the tables will be filled regardless.
    """,
    
    "Operator": """
    Appeals to the emotions. Soft Skillet was started by a group of restaurateurs because they dealt with the pain of poor 
    reservation management solutions on a regular basis. They'd been past users of OpenTable and Resy but felt like no one 
    ever understood what they actually wanted.
    """
}

async def analyze_product_fit(conversation_data):
    """Analyze which product pitch would best resonate with the customer"""
    try:
        prompt = f"""
        Analyze this sales conversation and conversation analysis to determine which of these three product pitches would best resonate with the customer.

        Conversation and Analysis Data:
        {json.dumps(conversation_data, indent=2)}

        Available Product Pitches:
        {json.dumps(PRODUCT_PITCHES, indent=2)}

        Consider:
        1. Customer Pain Points:
           - What problems did they express?
           - Which concerns were most emphasized?

        2. Customer Values:
           - What aspects of the solution excited them most?
           - What type of language/approach resonated with them?

        3. Conversation Context:
           - What was actually discussed vs what could have been discussed?
           - Were there missed opportunities?

        Provide analysis in the following JSON structure:
        {{
            "recommended_pitch": str,  # Name of the recommended product pitch
            "fit_score": float,  # 0.0 to 1.0
            "reasoning": {{
                "primary_reasons": [str],  # Key reasons this pitch would work best
                "customer_signals": [str],  # Specific signals from the conversation
                "potential_objections": [str]  # Possible concerns to address
            }},
            "actual_discussion": {{
                "alignment": str,  # How well the actual conversation aligned with the recommended pitch
                "missed_opportunities": [str],  # Key points that could have been emphasized
                "improvement_suggestions": [str]  # How to better position this product
            }},
            "alternative_pitches": [
                {{
                    "name": str,
                    "fit_score": float,
                    "key_consideration": str
                }}
            ]
        }}
        """

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert sales strategist analyzing conversation fit with product pitches."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Error analyzing product fit: {str(e)}")
        return None

async def process_file(file_path: Path):
    """Process a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis = await analyze_product_fit(data)
        if analysis:
            # Combine original data with product pitch analysis
            data['product_pitch_analysis'] = analysis
            return data
        return None

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

async def main(input_file=None):
    try:
        source_dir = Path('/Users/azadneenan/Documents/clipboard_health/transcription_summary')
        target_dir = Path('/Users/azadneenan/Documents/clipboard_health/pitch_recommendations')
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
        logger.critical(f"Error during product pitch analysis: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze product pitch effectiveness')
    parser.add_argument('--file', type=str, help='Path to specific JSON file to process')
    args = parser.parse_args()
    
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args.file)) 