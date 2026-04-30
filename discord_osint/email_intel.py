import re
import time
import subprocess as _sp
import os
import json
from . import utils
from .utils import resilient_task, tool_available, http_session
from .config import SMTP_CHECK, ENABLE_HOLEHE, ENABLE_H8MAIL, ENABLE_SCYLLA, ENABLE_GHUNT, ENABLE_EMAILREP, ENABLE_HIBP
from .scraping import is_valid_email, is_valid_personal_email

def generate_email_guesses(first, last, domains):
    guesses = []
    try:
        from permutations import email_permuter
        for d in domains:
            try: guesses.extend(email_permuter.all_email_permuter(first,last,d))
            except: guesses.extend(fallback_patterns(first,last,d))
    except ImportError:
        for d in domains: guesses.extend(fallback_patterns(first,last,d))
    return list(set(guesses))

def fallback_patterns(first, last, domain):
    f, l = first.lower(), last.lower()
    return [
        f"{f}@{domain}", f"{l}@{domain}",
        f"{f}.{l}@{domain}", f"{f}{l}@{domain}", f"{f}_{l}@{domain}",
        f"{f[0]}.{l}@{domain}", f"{f}.{l[0]}@{domain}", f"{f[0]}{l}@{domain}",
        f"{l}{f}@{domain}", f"{l}.{f}@{domain}", f"{l}_{f}@{domain}",
        f"{f}-{l}@{domain}", f"{l}-{f}@{domain}",
        f"{f[0]}{l[0]}@{domain}", f"{f[0]}-{l}@{domain}", f"{f}-{l[0]}@{domain}",
    ]

def verify_email_smtp(email):
    if not SMTP_CHECK: return True, None
    try:
        from validate_email import validate_email
    except ImportError: return False, "library missing"
    try:
        is_valid = validate_email(
            email, check_format=True, check_blacklist=True, check_dns=True,
            check_smtp=True, smtp_timeout=8, smtp_helo_host='my.host.name',
            smtp_from_address='check@example.org')
        return is_valid, None
    except Exception as e: return False, str(e)[:80]

@resilient_task(max_retries=2)
def run_holehe(email):
    if not tool_available("holehe"): return []
    cmd = ["holehe", email, "--only-used", "--no-color"]
    _, stdout, _ = utils.debug_subprocess(cmd, timeout=120)
    if stdout is None: return []
    sites = []
    for line in stdout.splitlines():
        if line.startswith("[+]") and not line.startswith("[+] Email used"):
            site = line[4:].strip()
            if site: sites.append(site)
    return sites

@resilient_task(max_retries=1)
def run_h8mail(email):
    if not tool_available("h8mail"): return ""
    cmd = ["h8mail", "-t", email]
    _, stdout, _ = utils.debug_subprocess(cmd, timeout=180)
    if stdout is None: return ""
    clean = re.sub(r'\x1b\[[0-9;]*m', '', stdout)
    if "Not Compromised" in clean:
        status = "clean"
    else:
        status = "compromised"
    return {"status": status, "raw": clean.strip()[:500]}

def run_gosearch(query):
    if not tool_available("gosearch"): return []
    try:
        res = _sp.run(["gosearch","-u",query], capture_output=True, text=True, timeout=20)
        if res.returncode==0 and res.stdout.strip():
            return [l.strip() for l in res.stdout.splitlines() if l.strip()]
    except Exception: pass
    return []

@resilient_task(max_retries=1)
def run_ghunt(gmail):
    ghunt_bin = os.path.expanduser("~/.local/bin/ghunt")
    if not os.path.exists(ghunt_bin) or not gmail.lower().endswith('@gmail.com'):
        return None
    cmd = [ghunt_bin, "email", gmail]
    _, stdout, _ = utils.debug_subprocess(cmd, timeout=60)
    if stdout is None: return None
    try:
        return json.loads(stdout) if isinstance(json.loads(stdout), dict) else {}
    except Exception as e:
        print(f"  GHunt error: {e}")
        return None

def check_hibp(email):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = http_session.get(f"https://haveibeenpwned.com/api/v2/breachedaccount/{email}", headers=headers, timeout=10)
        if r.status_code == 200: return r.json()
    except: pass
    return []

def check_emailrep(email):
    try:
        r = http_session.get(f"https://emailrep.io/{email}", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {"reputation": data.get("reputation"), "profiles": data.get("details",{}).get("profiles",[]), "data_breaches": data.get("details",{}).get("data_breaches",[])}
    except: pass
    return {}

def run_scylla(email):
    if not tool_available("scylla") or not ENABLE_SCYLLA:
        return ""
    cmd = ["scylla", "-e", email]
    _, stdout, _ = utils.debug_subprocess(cmd, timeout=60)
    if stdout is None:
        return ""
    return stdout.strip()[:500]
