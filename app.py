import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow requests from GitHub Pages

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent'

@app.route('/')
def index():
    return jsonify({ 'status': 'KariSpend proxy running' })

@app.route('/scan', methods=['POST'])
def scan():
    if not GEMINI_API_KEY:
        return jsonify({ 'error': 'API key not configured' }), 500

    data       = request.get_json()
    image_b64  = data.get('image_b64', '')
    categories = data.get('categories', [])
    item_memory = data.get('item_memory', {})

    if not image_b64:
        return jsonify({ 'error': 'No image provided' }), 400

    cat_list = ', '.join([f"{c['id']}:{c['name']}({c['icon']})" for c in categories])

    prompt = f"""You are a receipt reader for a Japanese household expense tracker.
Analyze this receipt image and extract all purchase data.

Available categories: {cat_list}

Known item→category mappings (use these if item matches): {json.dumps(item_memory)}

Return ONLY valid JSON, no other text, no markdown backticks:
{{
  "store": "store name in English if possible, otherwise as-is",
  "date": "YYYY-MM-DD",
  "items": [
    {{ "name": "item name in English", "price": 123, "catId": "category_id" }}
  ],
  "total": 999
}}

Rules:
- name: translate Japanese to English when obvious (にんじん→Carrot, バナナ→Banana, レジ袋大→Shopping Bag, オレンジ→Orange, マクラ→Pillow). Keep brand names as-is.
- price: integer only, no symbols
- catId: pick the best match from available categories. Use known mappings if item matches.
- total: grand total from receipt. If not visible, sum the items.
- date: extract from receipt (e.g. 2026年04月18日 → 2026-04-18). Use today if not found."""

    payload = {
        'contents': [{
            'parts': [
                {
                    'inline_data': {
                        'mime_type': 'image/jpeg',
                        'data': image_b64
                    }
                },
                {
                    'text': prompt
                }
            ]
        }],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 1024,
        }
    }

    try:
        resp = requests.post(
            f'{GEMINI_URL}?key={GEMINI_API_KEY}',
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()

        # Extract text from Gemini response
        text = result['candidates'][0]['content']['parts'][0]['text']
        # Strip any accidental markdown fences
        text = text.replace('```json', '').replace('```', '').strip()
        parsed = json.loads(text)

        return jsonify(parsed)

    except requests.exceptions.Timeout:
        return jsonify({ 'error': 'Request timed out' }), 504
    except requests.exceptions.RequestException as e:
        return jsonify({ 'error': f'Gemini API error: {str(e)}' }), 502
    except (KeyError, json.JSONDecodeError) as e:
        return jsonify({ 'error': f'Failed to parse response: {str(e)}' }), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
