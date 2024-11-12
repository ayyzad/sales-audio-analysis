import json
from pathlib import Path
import asyncio
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv
import argparse
import os
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def create_final_analysis(data):
    """Create final analysis for a single conversation"""
    try:
        prompt = f"""
        Create a focused analysis of this sales conversation based on the previous analyses.
        
        Conversation and Analysis Data:
        {json.dumps(data, indent=2)}

        Focus on:
        1. Key Insights - What are the most important patterns and findings from this conversation?
        2. Recommendations - What specific actions would improve this type of conversation?
        3. Summary - What's the overall assessment and main takeaway?

        Provide the analysis in the following JSON structure:
        {{
            "key_insights": [
                {{
                    "insight": str,
                    "evidence": str,
                    "impact": str
                }}
            ],
            "recommendations": [
                {{
                    "recommendation": str,
                    "rationale": str,
                    "expected_benefit": str
                }}
            ],
            "summary": str
        }}
        """

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert sales strategist focused on identifying key conversation insights and improvements."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Error creating final analysis: {str(e)}")
        return None

async def process_file(file_path: Path):
    """Process a single file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        analysis = await create_final_analysis(data)
        if analysis:
            data['final_analysis'] = analysis
            return data
        return None

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

async def main(input_file=None):
    try:
        source_dir = Path('/Users/azadneenan/Documents/clipboard_health/pitch_recommendations')
        target_dir = Path('/Users/azadneenan/Documents/clipboard_health/final_analysis')
        target_dir.mkdir(exist_ok=True)

        if input_file:
            # Process single file
            input_path = Path(input_file)
            logger.info(f"Processing: {input_path.name}")
            processed_data = await process_file(input_path)
            if processed_data:
                # Save JSON analysis
                output_path = target_dir / input_path.name
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, indent=2, ensure_ascii=False)
                
                # Create markdown summary
                summary_path = target_dir / f"{input_path.stem}_summary.md"
                with open(summary_path, 'w', encoding='utf-8') as f:
                    f.write(f"# Conversation Analysis Summary - {input_path.stem}\n\n")
                    
                    # Key Insights
                    f.write("## Key Insights\n\n")
                    for insight in processed_data['final_analysis']['key_insights']:
                        f.write(f"### {insight['insight']}\n")
                        f.write(f"**Evidence:** {insight['evidence']}\n")
                        f.write(f"**Impact:** {insight['impact']}\n\n")
                    
                    # Recommendations
                    f.write("## Recommendations to Improve Conversations\n\n")
                    for rec in processed_data['final_analysis']['recommendations']:
                        f.write(f"### {rec['recommendation']}\n")
                        f.write(f"**Rationale:** {rec['rationale']}\n")
                        f.write(f"**Expected Benefit:** {rec['expected_benefit']}\n\n")
                    
                    # Summary
                    f.write("## Overall Summary\n\n")
                    f.write(processed_data['final_analysis']['summary'])
                
                logger.info(f"Analysis saved: {output_path}")
                logger.info(f"Summary saved: {summary_path}")
        else:
            # Process all files in directory
            for json_file in source_dir.glob('*.json'):
                logger.info(f"Processing: {json_file.name}")
                processed_data = await process_file(json_file)
                if processed_data:
                    # Save JSON analysis
                    output_path = target_dir / json_file.name
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(processed_data, f, indent=2, ensure_ascii=False)
                    
                    # Create markdown summary
                    summary_path = target_dir / f"{json_file.stem}_summary.md"
                    with open(summary_path, 'w', encoding='utf-8') as f:
                        f.write(f"# Conversation Analysis Summary - {json_file.stem}\n\n")
                        
                        # Key Insights
                        f.write("## Key Insights\n\n")
                        for insight in processed_data['final_analysis']['key_insights']:
                            f.write(f"### {insight['insight']}\n")
                            f.write(f"**Evidence:** {insight['evidence']}\n")
                            f.write(f"**Impact:** {insight['impact']}\n\n")
                        
                        # Recommendations
                        f.write("## Recommendations to Improve Conversations\n\n")
                        for rec in processed_data['final_analysis']['recommendations']:
                            f.write(f"### {rec['recommendation']}\n")
                            f.write(f"**Rationale:** {rec['rationale']}\n")
                            f.write(f"**Expected Benefit:** {rec['expected_benefit']}\n\n")
                        
                        # Summary
                        f.write("## Overall Summary\n\n")
                        f.write(processed_data['final_analysis']['summary'])
                    
                    logger.info(f"Analysis saved: {output_path}")
                    logger.info(f"Summary saved: {summary_path}")

    except Exception as e:
        logger.critical(f"Error during analysis: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Create final analysis of conversations')
    parser.add_argument('--file', type=str, help='Path to specific JSON file to process')
    args = parser.parse_args()
    
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args.file)) 