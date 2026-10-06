# List Gemini Models

You can list available Gemini models via the Google API:

```bash
curl -s -H "Authorization: Bearer $GEMINI_API_KEY" "https://generativelanguage.googleapis.com/v1beta/openai/models" | jq -r '.data[].id'
```
