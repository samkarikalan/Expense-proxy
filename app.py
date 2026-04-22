import os
import json
import time
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
GEMINI_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent'

@app.route('/')
def index():
    return jsonify({'status': 'KariSpend proxy running'})

@app.route('/scan', methods=['POST'])
def scan():
    if not GEMINI_API_KEY:
        return jsonify({'error': 'API key not configured'}), 500

    data = request.get_json()
    image_b64 = data.get('image_b64', '')
    categories = data.get('categories', [])
    item_memory = data.get('item_memory', {})

    if not image_b64:
        return jsonify({'error': 'No image provided'}), 400

    cat_list = ', '.join([c['id'] + ':' + c['name'] + '(' + c['icon'] + ')' for c in categories])
    memory_json = json.dumps(item_memory)

    prompt = 'You are a receipt reader for a Japanese household expense tracker. Analyze this receipt image and extract all purchase data. Available categories: ' + cat_list + ' Known item-category mappings: ' + memory_json + ' Return ONLY valid JSON with no markdown: {"store": "store name", "date": "YYYY-MM-DD", "items": [{"name": "item name in English", "price": 123, "catId": "category_id"}], "total": 999} Rules: translate Japanese item names to English. price must be integer. Pick best catId from available categories. Extract date from receipt or use today. Sum items if total not visible.'

    payload = {
        'contents': [{
            'parts': [
                {'inline_data': {'mime_type': 'image/jpeg', 'data': image_b64}},
                {'text': prompt}
            ]
        }],
        'generationConfig': {
            'temperature': 0.1,
            'maxOutputTokens': 2048,
        }
    }

    last_error = ''
    for attempt in range(3):
        if attempt > 0:
            time.sleep(5 * attempt)
        try:
            resp = requests.post(
                GEMINI_URL,
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': GEMINI_API_KEY,
                },
                json=payload,
                timeout=45
            )

            if resp.status_code in [503, 429]:
                last_error = 'Gemini HTTP ' + str(resp.status_code) + ' (retrying...): ' + resp.text
                continue

            if not resp.ok:
                return jsonify({'error': 'Gemini HTTP ' + str(resp.status_code) + ': ' + resp.text}), 502

            result = resp.json()

            if 'candidates' not in result or not result['candidates']:
                return jsonify({'error': 'No candidates: ' + json.dumps(result)}), 500

            text = result['candidates'][0]['content']['parts'][0]['text']
            text = text.replace('```json', '').replace('```', '').strip()

            try:
                parsed = json.loads(text)
            except json.JSONDecodeError as e:
                return jsonify({'error': 'JSON parse failed: ' + str(e) + ' | Raw: ' + text[:300]}), 500

            return jsonify(parsed)

        except requests.exceptions.Timeout:
            last_error = 'Timeout on attempt ' + str(attempt + 1)
            continue
        except requests.exceptions.RequestException as e:
            error_body = e.response.text if hasattr(e, 'response') and e.response is not None else str(e)
            return jsonify({'error': 'Request error: ' + error_body}), 502
        except Exception as e:
            return jsonify({'error': 'Unexpected: ' + str(e)}), 500

    return jsonify({'error': 'Gemini unavailable after 3 attempts. ' + last_error}), 503


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
