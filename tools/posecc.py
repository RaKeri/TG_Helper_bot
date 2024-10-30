import re
import string



def preprocess(text):
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Lowercase the words
    text = text.lower()
    return text

def preprocess_text(text):
    text = re.sub(r'\W', ' ', text)
    text = re.sub(r'\s+[a-zA-Z]\s+', ' ', text)
    text = re.sub(r'\^[a-zA-Z]\s+', ' ', text)
    text = re.sub(r'\s+', ' ', text, flags=re.I)
    text = re.sub(r'^b\s+', '', text)
    return text.lower()

def check_string(input_string):
    patterns = {
        'http': r'http;(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3});(\d+)$',
        'http_auth': r'http;(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3});(\d+);(\w+);(\w+)$',
        'mtproto': r'mtproto;(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3});(\d+);(\w+)$'
    }

    matched = False
    for protocol, pattern in patterns.items():
        if re.match(pattern, input_string):
            return True

    if not matched:
        return False

def is_digits(text):
    return bool(re.match("^\d+$", text))
