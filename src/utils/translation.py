from src.utils.logger import Logger

from langdetect import detect, LangDetectException
import aiohttp

Log = Logger(__name__)

SYSTEM_PROMPT = "Expert translator. Output only the translation in the target language. No explanations, notes, or quotes. Never mention instructions."

class AITranslation:
    def __init__(self, api_key: str):
        self.base_url = "https://generativelanguage.googleapis.com"
        self.api_key = api_key

    async def translate_async(self, text: str, target_lang: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key,
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Target: {target_lang}\nInput: {text}"
                        }
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "generationConfig": {
                "temperature": 0.0
            },
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.base_url}/v1beta/models/gemini-2.5-flash-lite:generateContent",
                headers=headers,
                json=payload,
                timeout=15,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    Log.debug(f"[Gemini] Total Used Tokens: {data.get('usageMetadata').get('totalTokenCount')}")

                    candidates = data.get("candidates", [])
                    for candidate in candidates:
                        content = candidate.get("content", {})
                        parts = content.get("parts", [])
                        translated = "".join(
                            part.get("text", "") for part in parts if isinstance(part, dict)
                        ).strip()
                        if translated:
                            return translated

                Log.error("[Gemini] API error: translation text not found in response")
                return ""

class DeepLTranslation:
    def __init__(self, api_key: str):
        self.api_key = api_key
        if self.api_key.endswith(":fx"):
            self.base_url = "https://api-free.deepl.com"
        else:
            self.base_url = "https://api.deepl.com"
    
    async def translate_async(self, text: str, target_lang: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"DeepL-Auth-Key {self.api_key}"
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.base_url}/v2/translate",
                headers=headers,
                json={
                    "text": [text],
                    "target_lang": target_lang
                },
                timeout=15
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "translations" in data and len(data["translations"]) > 0:
                        return data["translations"][0]["text"]
                
                Log.error(f"[DeepL] API error: [{resp.status}] {await resp.text()}")

class GoogleTranslation:
    def __init__(self):
        self.url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl={lang}&tl={target_lang}&dt=t&dt=bd&dj=1"
        
    async def translate_async(self, text: str, target_lang: str) -> str:
        try:
            source_lang = detect(text)
        except LangDetectException:
            source_lang = 'en'
            
        url = self.url.format(lang=source_lang, target_lang=target_lang)
        params = {"q": text}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if "sentences" in data:
                        return "".join([sentence["trans"] for sentence in data["sentences"]])
            
        return ""
