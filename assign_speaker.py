import json
from pathlib import Path
import argparse

def relabel_speakers(transcript_data):
    # Create a mapping of speaker letters to names
    speaker_map = {
        assignment['speaker']: assignment['name']
        for assignment in transcript_data['speaker_assignments']
    }
    
    # Update each speaker in the speakers array
    for utterance in transcript_data['speakers']:
        # Add name while preserving the original speaker letter
        utterance['name'] = speaker_map[utterance['speaker']]
    
    return transcript_data

def process_single_file(input_path: Path, output_path: Path):
    print(f"Processing: {input_path.name}")
    
    # Read the source JSON file
    with open(input_path, 'r', encoding='utf-8') as f:
        transcript_data = json.load(f)
    
    # Relabel the speakers
    updated_data = relabel_speakers(transcript_data)
    
    # Save to new location
    output_path.parent.mkdir(exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_data, f, indent=2, ensure_ascii=False)
    
    print(f"Saved with speaker names: {output_path}")

def process_transcripts(input_path=None):
    if input_path:
        # Process single file
        input_path = Path(input_path)
        output_path = Path(__file__).parent / 'transcriptions_with_speaker' / input_path.name
        process_single_file(input_path, output_path)
    else:
        # Process all files in directory
        script_dir = Path(__file__).parent
        source_dir = script_dir / 'transcriptions'
        target_dir = script_dir / 'transcriptions_with_speaker'
        target_dir.mkdir(exist_ok=True)
        
        for json_file in source_dir.glob('*.json'):
            output_path = target_dir / json_file.name
            process_single_file(json_file, output_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process transcripts to add speaker names')
    parser.add_argument('--file', type=str, help='Path to specific JSON file to process')
    args = parser.parse_args()
    
    process_transcripts(args.file)