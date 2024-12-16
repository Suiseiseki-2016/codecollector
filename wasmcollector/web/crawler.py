import asyncio
import aiofiles
from playwright.async_api import async_playwright
from datetime import datetime
import os
from wasmcollector.web.response_handler import process_response


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.0 Safari/537.36"
WAIT_TIME = 5000
LOAD_EVENT_TIMEOUT = 30000000
SEED_FILE = "./seedlist.txt"

def timestamp():
    now = datetime.now()
    return f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] "

def ensure_url_scheme(url):
    """Ensure the URL has a scheme (http or https)."""
    if not url.startswith(("http://", "https://")):
        return f"http://{url}"
    return url

async def crawl_url(context, url, recursion_depth=0, max_depth=1, max_breadth=3):
    """Crawl a URL and optionally follow links recursively."""
    try:
        url = ensure_url_scheme(url)
        page = await context.new_page()
        print(f"{timestamp()}Crawling {url} (Depth: {recursion_depth})")

        wasm_folder = "./results/web/"
        if not os.path.exists(wasm_folder):
            os.makedirs(wasm_folder)

        # 设置请求拦截器
        async def handle_response(response):
            if response.ok and response.url.endswith(".wasm"):
                print(f"{timestamp()}Detected Wasm file: {response.url}")
                filename = os.path.join(wasm_folder, os.path.basename(response.url))
                content = await response.body()
                async with aiofiles.open(filename, mode="wb") as f:
                    await f.write(content)
                print(f"{timestamp()}Saved Wasm file: {filename}")

        page.on("response", handle_response)

        # 访问页面
        await page.goto(url, wait_until="networkidle", timeout=LOAD_EVENT_TIMEOUT / 1000)
        await page.wait_for_timeout(WAIT_TIME)

        # 递归抓取
        if recursion_depth < max_depth:
            links = await page.evaluate('''() => Array.from(document.querySelectorAll('a'), a => a.href)''')
            # 过滤无效链接并限制广度
            links = [ensure_url_scheme(link) for link in links if link.startswith("http")]
            for sub_url in links[:max_breadth]:
                await crawl_url(context, sub_url, recursion_depth + 1, max_depth, max_breadth)

        await page.close()
        print(f"{timestamp()}Finished crawling {url}")
    except Exception as e:
        print(f"{timestamp()}Error crawling {url}: {str(e)}")

async def main():
    try:
        if not os.path.exists(SEED_FILE):
            print("Seed file does not exist.")
            return

        if not os.path.exists("results"):
            os.makedirs("results")

        print(f"{timestamp()}Starting crawler.")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(user_agent=USER_AGENT)
            semaphore = asyncio.Semaphore(4)  # 控制并发量，减少资源占用
            batch_size = 10  # 每批次处理的种子 URL 数量

            async def safe_crawl(url):
                async with semaphore:
                    await crawl_url(context, url, max_depth=2, max_breadth=3)

            with open(SEED_FILE, 'r') as f:
                urls = f.read().strip().split("\n")

                # 分批次处理种子 URL
                for i in range(0, len(urls), batch_size):
                    batch_urls = urls[i:i + batch_size]
                    await asyncio.gather(*(safe_crawl(url) for url in batch_urls))

            await browser.close()
        print(f"{timestamp()}Crawler completed.")
    except KeyboardInterrupt:
        print(f"{timestamp()}Crawler interrupted by user.")
    
if __name__ == "__main__":
    asyncio.run(main())