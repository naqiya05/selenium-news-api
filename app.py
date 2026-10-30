"""
CSC418 - DevOps for Cloud Computing | Lab Assignment
Selenium news scraper + summarizer exposed as a REST API on port 7000.
Registration : FA23-BDS-064
News source  : ProPakistani   (064 % 20 + 1 = 5)
"""
import os
import re
from collections import Counter
import base64
import time
import base64
import time
from urllib.parse import quote_plus, urlparse, parse_qs, unquote, urlparse, parse_qs, unquote

from flask import Flask, jsonify, request
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

REGISTRATION = os.getenv("REGISTRATION", "FA23-BDS-064")
NEWS_SOURCE = "ProPakistani"
BASE_URL = "https://propakistani.pk"
ARTICLE_RE = re.compile(r"^https?://(www\.)?propakistani\.pk/\d{4}/\d{2}/\d{2}/[^/?#]+/?$")

app = Flask(__name__)


def make_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1366,900")
    opts.add_argument("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
    opts.page_load_strategy = "eager"
    chrome_bin = os.getenv("CHROME_BIN")
    if chrome_bin:
        opts.binary_location = chrome_bin
    driver_path = os.getenv("CHROMEDRIVER_PATH")
    if driver_path and os.path.exists(driver_path):
        driver = webdriver.Chrome(service=Service(driver_path), options=opts)
    else:
        driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    return driver


def _real_url(href):
    """Unwrap DuckDuckGo / Bing redirect links to the real article URL."""
    try:
        if "uddg=" in href:
            return unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
        if "bing.com/ck/a" in href:
            u = parse_qs(urlparse(href).query).get("u", [""])[0]
            if u.startswith("a1"):
                b = u[2:]
                return base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode()
    except Exception:
        pass
    return href


def _collect_links(driver):
    found, seen = [], set()
    for a in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
        href = _real_url((a.get_attribute("href") or "").strip()).split("#")[0]
        if ARTICLE_RE.match(href) and href not in seen:
            seen.add(href)
            found.append((href, (a.get_attribute("textContent") or "").strip()))
    return found


def _matches(href, text, keyword):
    terms = re.findall(r"[a-z0-9]+", keyword.lower()) or [keyword.lower()]
    hay = (href.replace("-", " ") + " " + text).lower()
    return any(re.search(r"\b" + re.escape(t) + r"\b", hay) for t in terms)


def _real_url(href):
    """Unwrap DuckDuckGo / Bing redirect links to the real article URL."""
    try:
        if "uddg=" in href:
            return unquote(parse_qs(urlparse(href).query).get("uddg", [""])[0])
        if "bing.com/ck/a" in href:
            u = parse_qs(urlparse(href).query).get("u", [""])[0]
            if u.startswith("a1"):
                b = u[2:]
                return base64.urlsafe_b64decode(b + "=" * (-len(b) % 4)).decode()
    except Exception:
        pass
    return href


def _collect_links(driver):
    found, seen = [], set()
    for a in driver.find_elements(By.CSS_SELECTOR, "a[href]"):
        href = _real_url((a.get_attribute("href") or "").strip()).split("#")[0]
        if ARTICLE_RE.match(href) and href not in seen:
            seen.add(href)
            found.append((href, (a.get_attribute("textContent") or "").strip()))
    return found


def _matches(href, text, keyword):
    terms = re.findall(r"[a-z0-9]+", keyword.lower()) or [keyword.lower()]
    hay = (href.replace("-", " ") + " " + text).lower()
    return any(re.search(r"\b" + re.escape(t) + r"\b", hay) for t in terms)


def find_first_result(driver, keyword):
    """Search the web for ProPakistani articles on the keyword and return the first result."""
    kw = quote_plus(keyword)
    slug = re.sub(r"[^a-z0-9]+", "-", keyword.lower()).strip("-")
    searches = [
        f"https://html.duckduckgo.com/html/?q=site%3Apropakistani.pk+{kw}",
        f"https://www.bing.com/search?q=site%3Apropakistani.pk+{kw}",
        f"{BASE_URL}/tag/{slug}/",
    ]
    fallback = None
    for url in searches:
        try:
            driver.get(url)
            time.sleep(3)
            if "not found" in (driver.title or "").lower():
                continue
            links = _collect_links(driver)
        except Exception:
            continue
        for href, text in links:
            if _matches(href, text, keyword):
                return href
        if links and fallback is None and "/tag/" in url:
            fallback = links[0][0]
    if fallback:
        return fallback
    try:
        driver.get(BASE_URL)
        time.sleep(3)
        links = _collect_links(driver)
        return links[0][0] if links else None
    except Exception:
        return None


def scrape_article(driver, url):
    driver.get(url)
    WebDriverWait(driver, 25).until(lambda d: d.find_elements(By.TAG_NAME, "p"))
    title = ""
    h1 = driver.find_elements(By.TAG_NAME, "h1")
    if h1:
        title = h1[0].text.strip()
    paragraphs = driver.find_elements(
        By.CSS_SELECTOR, ".entry-content p, .td-post-content p, article p, .post-content p")
    if not paragraphs:
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
    texts = []
    for p in paragraphs:
        t = p.text.strip()
        if len(t) > 40 and t not in texts:
            texts.append(t)
    return title, " ".join(texts)


STOPWORDS = set("""
a about above after again against all am an and any are as at be because been before
being below between both but by can could did do does doing down during each few for
from further had has have having he her here hers herself him himself his how i if in
into is it its itself just me more most my myself no nor not now of off on once only or
other our ours ourselves out over own same she should so some such than that the their
theirs them themselves then there these they this those through to too under until up
very was we were what when where which while who whom why will with would you your
yours yourself yourselves also said says per mr ms
""".split())


def summarize(text, max_sentences=3):
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) > 20]
    if len(sentences) <= max_sentences:
        return " ".join(sentences)
    words = re.findall(r"[a-zA-Z']+", text.lower())
    freq = Counter(w for w in words if w not in STOPWORDS and len(w) > 2)
    if not freq:
        return " ".join(sentences[:max_sentences])
    top = max(freq.values())
    scores = {}
    for i, s in enumerate(sentences):
        sw = [w for w in re.findall(r"[a-zA-Z']+", s.lower()) if w in freq]
        if sw:
            scores[i] = sum(freq[w] / top for w in sw) / (len(sw) ** 0.5)
            if i == 0:
                scores[i] *= 1.25
    best = sorted(sorted(scores, key=scores.get, reverse=True)[:max_sentences])
    return " ".join(sentences[i] for i in best)


@app.route("/")
def home():
    return f"""<!doctype html>
<html><head><title>News API - {REGISTRATION}</title></head>
<body style="font-family:sans-serif;max-width:700px;margin:40px auto">
  <h1>Registration Number: {REGISTRATION}</h1>
  <p>News source: <b>{NEWS_SOURCE}</b></p>
  <p>Try: <a href="/get?keyword=cricket">/get?keyword=cricket</a></p>
</body></html>"""


@app.route("/get", methods=["GET"])
def get_news():
    keyword = (request.args.get("keyword") or "").strip()
    result = {"registration": REGISTRATION, "newssource": NEWS_SOURCE,
              "keyword": keyword, "url": "", "summary": ""}
    if not keyword:
        result["summary"] = "Please provide a keyword, e.g. /get?keyword=cricket"
        return jsonify(result), 400
    driver = None
    try:
        driver = make_driver()
        url = find_first_result(driver, keyword)
        if not url:
            result["summary"] = f"No article found on {NEWS_SOURCE} for '{keyword}'."
            return jsonify(result), 200
        result["url"] = url
        title, body = scrape_article(driver, url)
        summary = summarize(body) if body else ""
        result["summary"] = summary or title or "Article text could not be extracted."
        return jsonify(result), 200
    except Exception as e:
        result["summary"] = f"Error while scraping: {type(e).__name__}: {e}"
        return jsonify(result), 500
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7000)
