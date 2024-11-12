import os
import json
import time
from dotenv import load_dotenv
import assemblyai as aai
from pathlib import Path

# Get the script's directory
SCRIPT_DIR = Path(__file__).parent.absolute()

# Load environment variables from .env in the same directory as the script
load_dotenv(SCRIPT_DIR / '.env')
api_key = os.getenv('ASSEMBLYAI_API_KEY')

# Initialize AssemblyAI client
aai.settings.api_key = api_key

def transcribe_audio_file(file_path):
    """
    Transcribe a single audio file and return the transcript
    """
    try:
        config = aai.TranscriptionConfig(
            speaker_labels=True
        )

        # Convert Path object to string
        file_path_str = str(file_path)

        transcript = aai.Transcriber().transcribe(
            file_path_str,  # Use string version of path
            config=config
        )

        return transcript
    except Exception as e:
        print(f"Error transcribing {file_path}: {str(e)}")
        return None

def save_transcript(transcript, original_file_path):
    """
    Save the transcript to a JSON file in the transcriptions directory
    """
    if transcript is None:
        return

    # Create transcriptions directory if it doesn't exist
    transcriptions_dir = SCRIPT_DIR / 'transcriptions'
    transcriptions_dir.mkdir(exist_ok=True)
    
    # Use same filename as audio but with .json extension in transcriptions directory
    output_path = transcriptions_dir / Path(original_file_path).name.replace(
        Path(original_file_path).suffix, '.json'
    )
    
    # Prepare data structure
    transcript_data = {
        'full_transcript': transcript.text,
        'speakers': [
            {
                'speaker': utterance.speaker,
                'text': utterance.text
            }
            for utterance in transcript.utterances
        ],
        'audio_file': Path(original_file_path).name,
        'transcribed_at': time.strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save as JSON
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

def main():
    # Audio directory path (relative to script location)
    audio_dir = SCRIPT_DIR / 'audio'
    
    # Supported audio extensions
    audio_extensions = {'.mp3', '.mov'}
    
    print(f"Looking for audio files in: {audio_dir}")
    
    # Process each audio file
    for file_name in os.listdir(audio_dir):
        if Path(file_name).suffix.lower() in audio_extensions:
            file_path = audio_dir / file_name
            print(f"Processing: {file_name}")
            
            transcript = transcribe_audio_file(file_path)
            
            if transcript:
                save_transcript(transcript, file_path)
                print(f"Transcription saved for: {file_name}")
            else:
                print(f"Failed to transcribe: {file_name}")

if __name__ == "__main__":
    main()
