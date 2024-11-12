import os
import json
from pathlib import Path
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
import logging
from dotenv import load_dotenv
import argparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env
load_dotenv()

# Initialize AsyncOpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

client = AsyncOpenAI(api_key=api_key)

async def process_batch(batch, full_transcript):
    """Process a batch of utterances with OpenAI API"""
    try:
        prompt = f"""
        Here is the full context of the conversation:
        {full_transcript}

        Now, analyze the sentiment of each utterance in the following conversation segments.
        Consider the full context above when determining the sentiment.
        For each utterance, determine:
        1. The overall sentiment (positive, negative, or neutral)
        2. A confidence score for the sentiment (0.0 to 1.0)

        Utterances to analyze:
        {json.dumps(batch, indent=2)}

        Provide your analysis in JSON format with the following structure:
        {{
            "analysis": [
                {{
                    "speaker": str,
                    "name": str,
                    "text": str,
                    "sentiment": str,
                    "confidence": float
                }}
            ]
        }}
        """

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an assistant that analyzes the sentiment of conversation utterances while considering the full context of the conversation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            response_format={"type": "json_object"}
        )
        
        response_content = response.choices[0].message.content
        logger.debug(f"API Response: {response_content}")
        
        processed_batch = json.loads(response_content)
        if 'analysis' not in processed_batch:
            logger.error(f"Unexpected response format. Response: {processed_batch}")
            return []
        
        return processed_batch['analysis']

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        logger.error(f"Raw response: {response_content}")
        return []
    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        logger.error(f"Exception details: {str(e)}")
        return []

async def process_file(file_path: Path):
    """Process a single JSON file"""
    try:
        # Read the input file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract speakers array and full transcript
        speakers = data.get('speakers', [])
        full_transcript = data.get('full_transcript', '')
        
        # Process in batches of 20
        batches = [speakers[i:i+20] for i in range(0, len(speakers), 20)]
        
        # Process all batches with full transcript context
        tasks = [process_batch(batch, full_transcript) for batch in batches]
        processed_batches = await asyncio.gather(*tasks)
        
        # Combine results
        processed_speakers = []
        for batch in processed_batches:
            processed_speakers.extend(batch)
        
        # Update the original data with sentiment analysis
        data['speakers'] = processed_speakers
        
        return data

    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return None

async def main(input_file=None):
    try:
        # Set up source and target directories
        source_dir = Path('/Users/azadneenan/Documents/clipboard_health/transcriptions_with_speaker')
        target_dir = Path('/Users/azadneenan/Documents/clipboard_health/trasncriptions_with_sentiment')
        target_dir.mkdir(exist_ok=True)

        if input_file:
            # Process single file
            input_path = Path(input_file)
            logger.info(f"Processing single file: {input_path.name}")
            
            processed_data = await process_file(input_path)
            
            if processed_data:
                output_path = target_dir / input_path.name
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(processed_data, f, indent=2, ensure_ascii=False)
                logger.info(f"Saved with sentiment analysis: {output_path}")
            else:
                logger.warning(f"Failed to process: {input_path.name}")
        else:
            # Process all files in directory
            for json_file in source_dir.glob('*.json'):
                logger.info(f"Processing: {json_file.name}")
                
                processed_data = await process_file(json_file)
                
                if processed_data:
                    output_path = target_dir / json_file.name
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(processed_data, f, indent=2, ensure_ascii=False)
                    logger.info(f"Saved with sentiment analysis: {output_path}")
                else:
                    logger.warning(f"Failed to process: {json_file.name}")

    except Exception as e:
        logger.critical(f"Error during sentiment analysis: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze sentiment in transcripts')
    parser.add_argument('--file', type=str, help='Path to specific JSON file to process')
    args = parser.parse_args()
    
    logging.getLogger().setLevel(logging.DEBUG)
    asyncio.run(main(args.file))