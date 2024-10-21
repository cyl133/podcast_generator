import openai
import os
import re
import json
from pydub import AudioSegment
import requests

client = openai.OpenAI(api_key='')
ELEVEN_LABS_API_KEY = ""

ELEVEN_LABS_VOICES = {
    'Host': 'cgSgspJ2msm6clMCkdW9',
    'Guest': 'iP95p4xoKVk53GoZ742B'
}

def read_article(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            article = file.read()
        return article
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

def generate_personas(article):
    prompt = f'''
Generate two diverse personas for a podcast discussing this news article:

\"\"\"
{article}
\"\"\"

For each persona, provide:
1. Name (THE HOST IS FEMALE AND GUEST IS MALE)
2. Role (Host or Guest)
3. Background (professional and personal)
4. Areas of expertise relevant to the article
5. Personality traits for engaging conversation
6. Speaking style (e.g., formal, casual, technical)
7. Potential biases or perspectives on the topic
8. Typical emotional responses or reactions

Output as a JSON list of two dictionaries, each containing the above fields.
'''
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert in creating diverse and engaging podcast personas."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.7
        )
        personas = json.loads(response.choices[0].message.content.strip())
        return personas
    except json.JSONDecodeError as e:
        print(f"Error parsing personas JSON: {e}")
        return None
    except Exception as e:
        print(f"Error generating personas: {e}")
        return None
def generate_podcast_script(article, personas):
    prompt = f'''
Create a strictly formatted podcast script based on the following article and personas:

Article:
\"\"\"
{article}
\"\"\"

Personas:
{json.dumps(personas, indent=2)}

Adhere to these STRICT formatting rules:
1. Always start dialogue with [Host]: or [Guest]:
2. Include a line break after each dialogue line.
4. Use quotation marks for actual dialogue.
7. Use <phoneme> tags for difficult pronunciations.
9. Use capitalization, duplicate letters like whaaaaaaaat and punctuations to emphasize EMOTIONS
9. Keep speaking turns short (1-3 sentences).

Example of correct formatting:
[Host]: "What do you think about the recent developments in North Korea? It seems the situation is escalating rapidly." 

[Guest]: "Well, Dr. Morrison, it's a grim prospect, to say the least. North Korea already likely possesses missiles capable of hitting key targets in South Korea and Japan. Overcoming the last remaining technological barriers would give them the ability to reach the U.S. mainland."

[Host]: "What do you think are the implications for international security?"

Create a natural, engaging conversation covering the article's main points. Aim for about 1500-2000 words total.
'''
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert podcast scriptwriter, skilled in creating engaging and natural dialogues with proper formatting."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=3000,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating podcast script: {e}")
        return None

def parse_script(script):
    pattern = r'\[(Host|Guest)\]:\s*(.*?)(?=\n\[|$)'
    matches = re.findall(pattern, script, re.DOTALL)
    return [(speaker, line.strip()) for speaker, line in matches if line.strip()]

def synthesize_speech_eleven_labs(text, voice_id, output_filename):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVEN_LABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        with open(output_filename, 'wb') as f:
            f.write(response.content)
        print(f'Audio content written to file "{output_filename}"')
    else:
        print(f"Error synthesizing speech: {response.status_code}")

def process_dialogues(dialogues):
    audio_files = []
    for i, (speaker, line) in enumerate(dialogues):
        output_filename = f"output_audio_{i:03d}_{speaker}.mp3"
        voice_id = ELEVEN_LABS_VOICES.get(speaker, ELEVEN_LABS_VOICES['Host'])
        synthesize_speech_eleven_labs(line, voice_id, output_filename)
        audio_files.append(output_filename)
    return audio_files

def combine_audio_files(audio_files):
    combined = AudioSegment.empty()
    for file in audio_files:
        sound = AudioSegment.from_mp3(file)
        combined += sound

    output_filename = 'podcast_output_elevenlabs2.mp3'
    combined.export(output_filename, format='mp3')
    print(f'Combined audio file saved as "{output_filename}"')
    return output_filename

def main():
    article = read_article('input_article.txt')
    if not article:
        return

    personas = generate_personas(article)
    if not personas:
        print("Failed to generate personas. Exiting.")
        return

    script = generate_podcast_script(article, personas)
    if not script:
        print("Failed to generate podcast script. Exiting.")
        return

    print("Generated Script:")
    print(script)

    dialogues = parse_script(script)
    if not dialogues:
        print("No dialogues found in the script. Exiting.")
        return

    print("\nParsed Dialogues:")
    for speaker, line in dialogues:
        print(f"[{speaker}]: {line}\n")

    audio_files = process_dialogues(dialogues)
    
    final_audio = combine_audio_files(audio_files)
    
    print(f"Podcast generated successfully: {final_audio}")

if __name__ == '__main__':
    main()