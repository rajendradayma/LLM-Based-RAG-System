import os
import requests
import time
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize API keys
SERPER_API_KEY = os.getenv('SERPER_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')


class CohereClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.cohere.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def generate(self, prompt, max_tokens=300):
        try:
            response = requests.post(
                f"{self.base_url}/generate",
                headers=self.headers,
                json={
                    "model": "command",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "k": 0,
                    "stop_sequences": [],
                    "return_likelihoods": "NONE"
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()["generations"][0]["text"]
        except Exception as e:
            print(f"Cohere API error: {str(e)}")
            return None


# Initialize Cohere client
cohere_client = CohereClient(COHERE_API_KEY) if COHERE_API_KEY else None


def search_articles(query):
    """Search for articles using Serper API."""
    if not SERPER_API_KEY:
        print("Serper API key not configured")
        return []

    headers = {
        'X-API-KEY': SERPER_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = {'q': query, 'num': 3}

    try:
        response = requests.post(
            'https://google.serper.dev/search',
            headers=headers,
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return [
            {
                'title': item.get('title', ''),
                'url': item['link'],
                'snippet': item.get('snippet', '')
            }
            for item in response.json().get('organic', [])[:3]
        ]
    except Exception as e:
        print(f"Error searching articles: {str(e)}")
        return []


def fetch_article_content(url):
    """Fetch article content with rotating user agents and delays."""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
    ]

    try:
        headers = {
            'User-Agent': user_agents[hash(url) % len(user_agents)],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }

        time.sleep(1)  # Respectful delay

        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'iframe', 'img', 'button', 'form']):
            element.decompose()

        # Extract meaningful content
        content = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'p', 'article', 'section']):
            text = tag.get_text().strip()
            if text and len(text.split()) > 3:
                if tag.name.startswith('h'):
                    content.append(f"\n\n{text}\n{'=' * len(text)}\n")
                else:
                    content.append(text)

        return ' '.join(content).strip() if content else "No readable content found"

    except Exception as e:
        print(f"Error fetching {url}: {str(e)}")
        return ""


def concatenate_content(articles):
    """Combine article contents with clear formatting."""
    if not articles:
        return "No articles found"

    return "\n\n".join(
        f"ARTICLE {i}: {art['title']}\nURL: {art['url']}\n"
        f"{fetch_article_content(art['url'])}\n{'=' * 50}"
        for i, art in enumerate(articles, 1) if art['url']
    )


def generate_answer(content, query):
    """Generate answer using Cohere API."""
    if not cohere_client:
        return "Cohere client not configured properly"

    try:
        prompt = f"""
        You are a helpful AI assistant. Answer the question based only on the following context.
        If you don't know the answer, just say you don't know. Don't make up answers.

        CONTEXT:
        {content[:5000]}  # Truncate to avoid hitting token limits

        QUESTION: {query}

        ANSWER:
        """

        response = cohere_client.generate(prompt)
        return response.strip() if response else "No response from Cohere API"
    except Exception as e:
        print(f"Error generating answer: {str(e)}")
        return "Sorry, I couldn't generate an answer due to an API error."


if __name__ == "__main__":
    # Test configuration
    test_query = "What is ChatGPT?"
    print(f"Testing with query: '{test_query}'")

    # Step 1: Search articles
    articles = search_articles(test_query)
    print(f"Found {len(articles)} articles")

    # Step 2: Concatenate content
    content = concatenate_content(articles)
    print(f"Content length: {len(content)} characters")

    # Step 3: Generate answer
    if content and len(content) > 100:  # Minimum content threshold
        answer = generate_answer(content, test_query)
        print("\nGenerated Answer:")
        print(answer)
    else:
        print("\nFailed to generate answer:")
        print("- No sufficient content" if len(content) <= 100 else "- Cohere client not working")