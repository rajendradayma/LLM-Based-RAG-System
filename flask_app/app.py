from flask import Flask, request, jsonify
from utils import search_articles, concatenate_content, generate_answer
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)


@app.route('/query', methods=['POST'])
def handle_query():
    """Endpoint that handles the RAG pipeline"""
    try:
        # Get JSON data from request
        data = request.get_json()

        # Validate request
        if not data or 'query' not in data:
            return jsonify({'error': 'Missing query parameter'}), 400

        query = data['query'].strip()
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400

        # Step 1: Search articles
        articles = search_articles(query)
        if not articles:
            return jsonify({
                'answer': 'No relevant articles found',
                'sources': []
            })

        # Step 2: Process content
        content = concatenate_content(articles)
        if len(content) < 100:
            return jsonify({
                'answer': 'Insufficient content to generate answer',
                'sources': [art['url'] for art in articles]
            })

        # Step 3: Generate answer
        answer = generate_answer(content, query)

        # Return successful response
        return jsonify({
            'answer': answer,
            'sources': [art['url'] for art in articles],
            'status': 'success'
        })

    except Exception as e:
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


if __name__ == '__main__':
    app.run(host='localhost', port=5001, debug=True)
