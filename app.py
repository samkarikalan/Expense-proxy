import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(**name**)
CORS(app)

GEMINI_API_KEY = os.environ.get(‘GEMINI_API_KEY’)
GEMINI_URL = ‘https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent’

@app.route(’/’)
def index():
return jsonify({‘status’: ‘KariSpend proxy running’})

@app.route(’/scan’, methods=[‘POST’])
def scan():
if not GEMINI_API_KEY:
return jsonify({‘error’: ‘API key not configured’}), 500

```
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
        'maxOutputTokens': 1024,
    }
}

try:
    resp = requests.post(
        GEMINI_URL,
        headers={
            'Content-Type': 'application/json',
            'x-goog-api-key': GEMINI_API_KEY,
        },
        json=payload,
        timeout=30
    )

    if not resp.ok:
        return jsonify({'error': 'Gemini error ' + str(resp.status_code) + ': ' + resp.text}), 502

    result = resp.json()
    text = result['candidates'][0]['content']['parts'][0]['text']
    text = text.replace('```json', '').replace('```', '').strip()
    parsed = json.loads(text)
    return jsonify(parsed)

except requests.exceptions.Timeout:
    return jsonify({'error': 'Request timed out'}), 504
except requests.exceptions.RequestException as e:
    error_body = e.response.text if hasattr(e, 'response') and e.response is not None else str(e)
    return jsonify({'error': 'Gemini API error: ' + error_body}), 502
except (KeyError, json.JSONDecodeError) as e:
    return jsonify({'error': 'Failed to parse response: ' + str(e)}), 500
```

if **name** == ‘**main**’:
port = int(os.environ.get(‘PORT’, 5000))
app.run(host=‘0.0.0.0’, port=port)
