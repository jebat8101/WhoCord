import re
import time
import subprocess as _sp
import os
import json
import dns.resolver
import smtplib
import socket
import hashlib
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
    _, stdout, _ = utils.run_external_tool("holehe", email, "--only-used", "--no-color", timeout=120)
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
    _, stdout, _ = utils.run_external_tool("h8mail", "-t", email, timeout=180)
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
    except Exception:
        if utils.DEBUG_MODE:
            print("  GHunt: upstream parsing error (known issue) – skipped.")
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

import re

def _strip_ansi(text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def run_scylla(email):
    if not tool_available("scylla") or not ENABLE_SCYLLA:
        return ""
    _, stdout, _ = utils.run_external_tool("scylla", "-l", email, timeout=60)
    if not stdout:
        return ""

    # Strip ANSI control sequences
    stdout = _strip_ansi(stdout)

    # Skip all banner lines until we hit a meaningful result line
    lines = stdout.splitlines()
    useful_lines = []
    started = False
    for line in lines:
        # Detect the start of the actual result or an error
        if not started:
            if (
                "[*] Searching" in line or
                "Traceback" in line or
                "TypeError" in line or
                "Error" in line or
                line.strip().startswith("usage:") or
                line.strip().startswith("scylla.py:")
            ):
                started = True
                useful_lines.append(line)
                continue
        else:
            useful_lines.append(line)

    clean = "\n".join(useful_lines).strip()
    if not clean:
        return "Scylla ran but produced no output."
    return clean[:500]

# ---- New advanced email enrichment functions ----
def check_mx_record(domain):
    """Return list of MX hostnames for a domain."""
    try:
        answers = dns.resolver.resolve(domain, 'MX')
        return [str(r.exchange).rstrip('.') for r in answers]
    except Exception:
        return []

def verify_email_smtp_advanced(email):
    """
    Verify email existence using SMTP RCPT TO.
    Returns dict with 'valid' (True/False/None) and 'reason'.
    """

    domain = email.split('@')[1]
    mx_records = check_mx_record(domain)
    if not mx_records:
        return {'valid': False, 'reason': 'No MX record'}

    mx_host = mx_records[0]
    try:
        with smtplib.SMTP(mx_host, 25, timeout=10) as smtp:
            smtp.helo(socket.gethostname())
            smtp.mail('verify@example.com')
            code, message = smtp.rcpt(email)
            if code == 250:
                return {'valid': True, 'reason': ''}
            else:
                return {'valid': False, 'reason': f'SMTP: {code} {message.decode()}'}
    except Exception as e:
        return {'valid': None, 'reason': str(e)}

def gravatar_lookup(email):
    """Return Gravatar image URL if an account exists."""
    email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{email_hash}?d=404&s=200"
    try:
        r = http_session.get(url)
        if r.status_code == 200 and 'image' in r.headers.get('Content-Type', ''):
            return url
    except Exception:
        pass
    return None
