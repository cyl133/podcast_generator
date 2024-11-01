import os
import json
import openai
import time

# Initialize OpenAI client with your API key
client = openai.OpenAI(api_key='')

# Function to load the news article from a plain text file
def load_news_article(file_path: str) -> str:
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

# Function to load the discussion from a saved chat summary file
def load_discussion(file_path: str) -> str:
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return "No discussion content found."

# Function to generate the podcast script based on the article and discussion
def generate_podcast_script(article_content: str, discussion: str) -> str:
    prompt = f"""
Using the following discussion and news article, create a podcast script between two persons that delves into future predictions and the impact of the news.

Article Content:
\"\"\"
{article_content}
\"\"\"

Discussion:
\"\"\"
{discussion}
\"\"\"

Adhere to these STRICT formatting rules:
1. Start each dialogue with [Speaker]: (Speaker 1 or Speaker 2)
2. Include a line break after each dialogue line.
3. Use quotation marks for actual dialogue.
4. Keep speaking turns short (1-3 sentences).
5. Do not include any additional text or explanations.
6. The script should be strictly in dialogue form between Speaker 1 and Speaker 2.

Aim for about 1500-2000 words total.

Provide only the podcast script in the specified format.
"""
    print("Generating podcast script...")
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are an expert podcast scriptwriter."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    return response.choices[0].message.content.strip()

# Main function to orchestrate loading, generating, and saving the podcast script
def main():
    # Load the news article content
    news_article_content = load_news_article("input_article.txt")
    # Load the saved discussion
    discussion_content = load_discussion("chat_summary.txt")
    # Generate the podcast script
    podcast_script = generate_podcast_script(news_article_content, discussion_content)

    # Save the podcast script to a file
    with open('podcast_script.txt', 'w', encoding='utf-8') as f:
        f.write(podcast_script)
    print("Podcast script saved to 'podcast_script.txt'")

# Entry point
if __name__ == '__main__':
    main()
