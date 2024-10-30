import requests

class GoogleTranslator:
    def __init__(self):
        self.api_key = "AIzaSyBOti4mM-6x9WDnZIjIeyEU21OpBXqWBgw"
        self.detect_url = 'https://translation.googleapis.com/language/translate/v2/detect'
        self.translate_url = 'https://translation.googleapis.com/language/translate/v2'

    def detect_language(self, text):
        params = {
            'key': self.api_key,
            'q': text,
        }
        response = requests.post(self.detect_url, data=params)
        result = response.json()

        return result['data']['detections'][0][0]['language']

    async def translate_text(self, text, target_language):
        source_language = self.detect_language(text)
        params = {
            'key': self.api_key,
            'q': text,
            'source': source_language,
            'target': target_language,
            'format': 'text'
        }
        response = requests.post(self.translate_url, data=params)
        result = response.json()
        try:
            return result['data']['translations'][0]['translatedText']
        except:
            return text