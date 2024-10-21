import openai
import os
import re
import json
from pydub import AudioSegment
import requests
from io import BytesIO

client = openai.OpenAI(api_key='')

def read_article(file_path):
    with open(file_path, 'r') as file:
        article = file.read()
    return article

def generate_personas(article):
    prompt = f'''
You are to generate two personas for a podcast discussing the following news article:

\"\"\"
{article}
\"\"\"

Each persona should have the following attributes:
- name
- role (Host or Guest)
- background: A brief description of their professional and personal background.
- expertise: Areas of expertise relevant to the article.
- personality Traits: Traits that will make the conversation engaging.

Provide the output in valid JSON format as a list of two dictionaries.
'''
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates personas for podcasts."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )

    personas_json = response.choices[0].message.content.strip()
    print("OpenAI Response:", personas_json)

    if personas_json.startswith('```json'):
        personas_json = personas_json[7:]
    if personas_json.endswith('```'):
        personas_json = personas_json[:-3]

    print("Cleaned Personas JSON:", personas_json)

    if not personas_json:
        print("Received empty or invalid response from OpenAI API.")
        return None

    return personas_json

def generate_podcast_script(article, personas):
    prompt = f'''
You are to write a podcast script based on the following news article and personas.

News Article:
\"\"\"
{article}
\"\"\"

Personas:
{personas}

Instructions:
- Write the script as a dialogue between the Host and the Guest.
- The conversation should be engaging, natural, and discuss the key points of the article.
- Include interactions, reactions, and verbal fillers to enhance naturalness.
- Output the script in the following format:

[Host]: Host's dialogue goes here.

[Guest]: Guest's dialogue goes here.

Ensure each dialogue turn starts with the speaker label in square brackets, followed by a colon.
'''
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that generates podcast scripts."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000,
        temperature=0.7
    )
    script = response.choices[0].message.content.strip()
    return script

def parse_personas(personas_json):
    try:
        personas = json.loads(personas_json)
        return personas
    except json.JSONDecodeError as e:
        print(f"Error parsing personas JSON: {e}")
        return None

def parse_script(script):
    pattern = r'\[(Host|Guest)\]:\s*(.*?)(?=\n\[|$)'
    matches = re.findall(pattern, script, re.DOTALL)
    dialogues = []
    for speaker, line in matches:
        dialogues.append((speaker, line.strip()))
    return dialogues

def synthesize_speech(text, output_filename, voice):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    response.stream_to_file(output_filename)
    print(f'Audio content written to file "{output_filename}"')

def combine_audio_files(audio_files, output_filename):
    combined = AudioSegment.empty()
    for file in audio_files:
        sound = AudioSegment.from_mp3(file)
        combined += sound
    combined.export(output_filename, format='mp3')
    print(f'Combined audio file saved as "{output_filename}"')

def main():
    # Read the input article
    article = read_article('input_article.txt')

    # Generate personas
    personas_json = generate_personas(article)
    print("Generated Personas JSON:")
    print(personas_json)

    # Parse personas
    personas = parse_personas(personas_json)
    if not personas:
        print("Failed to parse personas. Exiting.")
        return

    # Map personas to voices
    voice_map = {
        'Host': 'alloy',  # A neutral voice
        'Guest': 'nova'   # A different voice for contrast
    }

    # Generate podcast script
    script = generate_podcast_script(article, personas_json)
    print("Generated Script:")
    print(script)

    # Parse the script
    dialogues = parse_script(script)
    if not dialogues:
        print("No dialogues found in the script. Exiting.")
        return

    print("Parsed Dialogues:")
    for speaker, line in dialogues:
        print(f"[{speaker}]: {line}")

    # Synthesize speech and collect audio file names
    audio_files = []
    for i, (speaker, line) in enumerate(dialogues):
        output_filename = f"output_audio_{i}_{speaker}.mp3"
        voice = voice_map.get(speaker, 'alloy')
        synthesize_speech(line, output_filename, voice)
        audio_files.append(output_filename)

    # Combine audio files into one
    combine_audio_files(audio_files, 'podcast_output.mp3')

if __name__ == '__main__':
    main()