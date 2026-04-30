import re
import tempfile
import os
import json
import subprocess as _sp
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from . import utils                              # <-- NEEDED for debug
from .utils import http_session, github_session, resilient_task
from .config import SKIP_GITHUB, GITHUB_TOKEN, ENABLE_SOCID, ENABLE_GITFIVE

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

DOMAINS_TO_SKIP_GENERIC = {
    "accounts.google.com", "docs.github.com", "api.github.com", "collector.github.com",
    "gql.twitch.tv", "assets.twitch.tv", "codecademy.com", "youtube.com/s/",
    "youtube.com/error_204/", "youtube.com/csi_204/", "youtube.com/about/",
    "youtube.com/creators/", "youtube.com/howyoutubeworks?",
    "github.com/security", "github.com/orgs", "github.com/newrelic",
    "github.com/greasyfork-org", "github.com/ppy", "github.com/tetrio",
    "github.com/truckersmp", "github.com/mcp", "github.com/collections",
    "github.com/trending", "github.com/customer-stories", "github.com/sponsors",
    "github.com/enterprise", "github.com/features", "github.com/pricing",
    "github.com/accelerator", "github.com/partners", "github.com/premium-support",
    "github.com/trust-center", "github.com/why-github",
}

BANNED_NAME_PHRASES = {
    "greasy fork","uuid javascript module","new relic","bootstrap","grav","codewars","tetr.io",
    "mastodon","keybase","liberapay","alpine iq","org","com","net","user","users","account",
    "sign in","sign up","login","log in","security measure","profile not available",
    "imgur the magic of the internet","image shack","revolut me","fansly",
    "search for the best onlyfans creators",
    "a paradise of lost thoughts and love that is found",
    "the roadmap that changes runescape forever",
    "setup a network namespace with internet access","keybase io.md",
    "understanding github code search syntax","sign in to github","keyboard shortcuts",
    "reporting abuse or spam","github terms of service","github general privacy statement",
    "blocking a user from your personal account","houzz tv","chess.com","sentimente.ro",
    "flickr","docker","envato","stream elements","teletype",
    "client challenge","castingcallclub","truth social","1of1photography","meh",
    "twitter share url","facebook share url","livejournal redirect"
}

GENERIC_WORDS = {"the","and","for","you","your","this","that","with","from","they","will",
                 "have","not","are","can","had","been","were","did","does","has","its","each",
                 "all","many","more","most","other","some","such","what","them","then","than"}

def is_likely_profile_url_v2(url: str) -> bool:
    try: parsed = urlparse(url)
    except: return False
    path = parsed.path.lower()
    domain = parsed.netloc.lower()
    if re.search(r'\.(js|css|png|jpe?g|gif|svg|ico|webp|woff2?|json|xml|pdf|zip|gz|bz2|rar|7z|mp[34]|mov|avi)$', path):
        return False
    if any(domain.endswith(d) for d in DOMAINS_TO_SKIP_GENERIC): return False
    if not re.search(r'/(users?|u|@|profile|channel|id)/[^/]+', url.lower()):
        clean_path = path.strip('/')
        if not clean_path or '/' in clean_path or '?' in clean_path or len(clean_path) < 3:
            return False
    return True

def looks_like_real_name_v2(name: str) -> bool:
    if not isinstance(name, str): return False
    s = name.strip()
    if len(s) < 2 or len(s) > 40: return False
    if any(c.isdigit() for c in s): return False
    if s.count(',') > 0: return False
    low = s.lower()
    if low in BANNED_NAME_PHRASES: return False
    words = s.split()
    if len(words) > 3: return False
    # Accept single-word names if they start with an uppercase letter and are not generic words
    if len(words) == 1:
        w = words[0]
        if re.fullmatch(r'[A-ZÀ-ÿ][a-zà-ÿ]+([A-Z][a-zà-ÿ]+)*', w):  # allows CamelCase
            if w.lower() in GENERIC_WORDS and w.lower() not in {"will","may","june","rose","chase","hope"}:
                return False
            return True
        return False
    # 2‑3 word names: existing logic
    for w in words:
        if re.fullmatch(r'[A-Z]\.?', w): continue
        if not re.fullmatch(r"[A-ZÀ-ÿ][a-zà-ÿ]+(['\-][A-Za-zà-ÿ]+)*", w):
            return False
        if len(w) > 1 and w.lower() in GENERIC_WORDS:
            if w.lower() in {"will", "may", "june", "rose", "chase", "hope"}:
                continue
            return False
    return True

def is_valid_email(email):
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email): return False
    domain = email.split('@')[1].lower()
    bad_tlds = {'jpg','jpeg','png','gif','svg','bmp','ico','mp4','mov','avi','css','js','json','xml','pdf','doc','xls','zip','gz','bz2','rar','7z','webp','mp3','wav','flac'}
    if '.' not in domain: return False
    tld = domain.rsplit('.',1)[-1]
    return tld not in bad_tlds

# -------------------------------------------------------------------
#  NEW PERSONAL EMAIL FILTER – much stricter
# -------------------------------------------------------------------
# Emails that are obviously fake/test/noise
_EXTRA_BAD_EMAILS = {
    "email@example.com",
    "test@example.com",
    "hello+support@hashnode.com",
    "git@hf.co",
    "support@hashnode.com",
}

def is_valid_personal_email(email: str) -> bool:
    """Return True only if the email looks like a real personal address."""
    if not is_valid_email(email):
        return False
    local, domain = email.split('@', 1)
    domain = domain.lower()

    # reject obvious test domains
    if domain in {"example.com", "example.org", "test.com", "test.org"}:
        return False

    # reject known bad addresses
    if email.lower() in _EXTRA_BAD_EMAILS:
        return False

    if domain.startswith("www."):
        return False

    # reject role‑based or sub‑addressed like "hello+support@"
    if "+" in local:
        return False
    if local.lower() in {"hello", "contact", "info", "support", "admin",
                         "help", "noreply", "no-reply", "0_10_",
                         "mailbox", "email", "webmaster", "postmaster"}:
        return False

    # purely numeric local parts are usually not personal
    if local.isdigit():
        return False

    # long hex strings (like Sentry identifiers)
    if re.search(r'^[a-f0-9]{20,}$', local):
        return False

    # known noisy domains (unchanged)
    noisy_domains = {"mixcloud.com", "discogs.com", "etsy.com", "ebay.com",
                     "poshmark.com", "freelancer.com", "flickr.com",
                     "soundcloud.com", "sourceforge.net", "bandcamp.com",
                     "archive.org", "google.com", "huggingface.co",
                     "lichess.org", "stackoverflow.com", "github.com",
                     "gitlab.com", "bitbucket.org"}
    if domain in noisy_domains:
        return False

    # everything else is considered potentially personal
    return True

# -------------------------------------------------------------------
#  REST OF THE FILE (unchanged except import and debug in extractor)
# -------------------------------------------------------------------
@resilient_task(max_retries=1)
def run_socid_extractor(html: str) -> dict:
    """Extract identity data from HTML using the socid_extractor library directly."""
    try:
        import socid_extractor
        result = socid_extractor.extract(html)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}

@resilient_task(max_retries=2)
def scrape_profile_info(platform, username):
    info = {"name":"","email":"","bio":"","blog":"","socid":None,"avatar":None}
    if platform in {"facebook", "instagram", "tiktok", "pinterest", "snapchat", "linkedin"}:
        return info
    headers = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    if platform=="github":
        if SKIP_GITHUB: return info
        gh_headers = headers.copy()
        if GITHUB_TOKEN: gh_headers["Authorization"] = f"token {GITHUB_TOKEN}"
        try:
            r = github_session.get(f"https://api.github.com/users/{username}", headers=gh_headers, timeout=10)
            if r.status_code==200:
                data = r.json()
                info["name"] = data.get("name") or ""
                raw_email = data.get("email") or ""
                if raw_email and is_valid_personal_email(raw_email):
                    info["email"] = raw_email
                info["bio"] = data.get("bio") or ""
                info["blog"] = data.get("blog") or ""
                info["avatar"] = data.get("avatar_url")
                if not info["email"] and info["bio"]:
                    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', info["bio"])
                    personal_emails = [e for e in emails if is_valid_personal_email(e)]
                    if personal_emails: info["email"] = personal_emails[0]
                if ENABLE_SOCID:
                    try:
                        html_resp = http_session.get(data.get("html_url"), headers=headers, timeout=10)
                        if html_resp.status_code==200:
                            info["socid"] = run_socid_extractor(html_resp.text)
                    except: pass
        except Exception as e: print(f"  GitHub scrape error {username}: {e}")
        return info

    clean_user = username.lstrip("@") if platform=="youtube" else username
    url_map = {
        "twitter": f"https://twitter.com/{clean_user}",
        "instagram": f"https://instagram.com/{clean_user}",
        "tiktok": f"https://tiktok.com/@{clean_user}",
        "reddit": f"https://reddit.com/user/{clean_user}",
        "youtube": f"https://youtube.com/@{clean_user}",
    }
    if platform in url_map:
        try:
            r = http_session.get(url_map[platform], headers=headers, timeout=10)
            if r.status_code==200:
                if ENABLE_SOCID:
                    info["socid"] = run_socid_extractor(r.text)
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
                if emails:
                    personal_emails = [e for e in emails if is_valid_personal_email(e)]
                    if personal_emails: info["email"] = personal_emails[0]
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(r.text, 'html.parser')
                    og_image = soup.find("meta", property="og:image")
                    if og_image: info["avatar"] = og_image.get("content")
                    if platform=="twitter":
                        name_tag = soup.find("div", {"data-testid":"UserName"})
                        if name_tag: info["name"] = (name_tag.text.strip() or "")
                except ImportError:
                    m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
                    if m: info["avatar"] = m.group(1)
        except Exception as e:
            print(f"  Scrape error {platform}/{username}: {e}")
    return info

@resilient_task(max_retries=1)
def scrape_generic_url(url):
    info = {"name":"","email":"","bio":"","blog":url,"socid":None,"avatar":None}
    try:
        domain = urlparse(url).netloc.lower()
    except:
        return info
    if any(domain.endswith(d) for d in {"facebook.com", "instagram.com", "tiktok.com", "pinterest.com", "snapchat.com", "linkedin.com"}):
        return info
    if not is_likely_profile_url_v2(url):
        return info
    headers = {"User-Agent":"Mozilla/5.0"}
    try:
        r = http_session.get(url, headers=headers, timeout=10)
        if r.status_code==200:
            if ENABLE_SOCID: info["socid"] = run_socid_extractor(r.text)
            emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r.text)
            for email in emails:
                if is_valid_personal_email(email):
                    info["email"] = email; break
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'html.parser')
                og_img = soup.find("meta", property="og:image")
                if og_img: info["avatar"] = og_img.get("content")
            except: pass
    except: pass
    return info

def is_likely_github_user(slug):
    if len(slug) < 2:
        return False
    if '-' in slug and len(slug) > 15:
        return False
    if slug in {"security","mcp","orgs","collections","trending","customer-stories","sponsors",
                "enterprise","features","pricing","topics","marketplace","solutions","resources",
                "newrelic","truckersmp","ppy","tetrio","greasyfork-org"}:
        return False
    return True

@resilient_task(max_retries=1)
def run_gitfive(github_username):
    if not ENABLE_GITFIVE:
        return {}
    cmd = ["gitfive", "user", github_username, "--json"]
    _, stdout, _ = utils.debug_subprocess(cmd, timeout=120)
    if stdout is None:
        return {}
    try:
        data = json.loads(stdout)
        return data if isinstance(data, dict) else {}
    except Exception as e:
        print(f"  GitFive error: {e}")
        return {}
