from datetime import date
from hashlib import sha256
from urllib.parse import urlparse
import os

recent_js_files = []
out_dir = "./results/web/"

def process_response(flow):
    global recent_js_files
    keywords = {"wasm": []}
    wasm_keywords = keywords.get("wasm", [])

    recent_js_files = recent_js_files[-100:]
    domain = urlparse(flow["request"]["url"]).netloc

    buffer = flow["response"].get("content", b"")
    if buffer[:4] == b'\x00asm':
        hash_val = sha256(buffer).hexdigest()
        filename = f"{domain.replace('.', '_')}_{hash_val[:16]}"
        os.makedirs(out_dir, exist_ok=True)
        with open(f"{out_dir}{filename}.wasm", 'wb') as out:
            out.write(buffer)
        with open(f"{out_dir}{filename}.meta", 'w') as out:
            out.write(f"file: {filename}.wasm\n")
            out.write(f"url: {flow['request']['url']}\n")
            out.write(f"date: {str(date.today())}\n")
            out.write(f"content-type: {flow['response'].get('content-type', '')}\n")
            out.write(f"related-js: {recent_js_files}\n")
            out.write(f"method: crawler-mitmproxy\n")

    elif flow["request"]["url"].endswith(".js"):
        recent_js_files.append((domain, flow["request"]["url"]))
        text = buffer.decode("utf-8", errors="ignore")
        if any(keyword in text for keyword in wasm_keywords):
            hash_val = sha256(bytes(text, "utf-8")).hexdigest()
            filename = f"{domain.replace('.', '_')}_{hash_val[:16]}"
            with open(f"{out_dir}{filename}.js", 'w') as out:
                out.write(text)