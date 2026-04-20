# KariSpend Proxy

Flask backend that proxies receipt image scanning via Google Gemini Vision API.

## Deploy to Render

1. Push this folder to a new GitHub repo (e.g. `karispend-proxy`)
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
5. Add environment variable:
   - Key: `GEMINI_API_KEY`
   - Value: your Google AI Studio API key
6. Deploy — your URL will be `https://karispend-proxy.onrender.com`

## Endpoint

`POST /scan`

Request body:
```json
{
  "image_b64": "<base64 encoded image>",
  "categories": [{ "id": "veg", "name": "Vegetables", "icon": "🥦" }],
  "item_memory": { "carrot": "veg" }
}
```

Response:
```json
{
  "store": "Maruetsu",
  "date": "2026-04-18",
  "items": [
    { "name": "Carrot", "price": 259, "catId": "veg" }
  ],
  "total": 1144
}
```
