import urllib.request
import urllib.parse
import os

text = "Hello, this is a real connection test."
encoded = urllib.parse.quote(text)
url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={encoded}&tl=en&client=tw-ob"
file_name = "speech_test.mp3"

req = urllib.request.Request(
    url, 
    headers={'User-Agent': 'Mozilla/5.0'}
)

print(f"Downloading {file_name} from Google TTS...")
try:
    with urllib.request.urlopen(req) as response, open(file_name, 'wb') as out_file:
        data = response.read()
        out_file.write(data)
    print(f"Downloaded {file_name}, size: {os.path.getsize(file_name)} bytes")
except Exception as e:
    print(f"Failed to download: {e}")
