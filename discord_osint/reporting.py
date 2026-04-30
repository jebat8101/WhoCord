import json
import re
import os
import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from .scraping import looks_like_real_name_v2, is_valid_email

# -------------------------------------------------------------------
#  Identity confidence scoring (unchanged)
# -------------------------------------------------------------------
def calculate_identity_confidence(intel):
    dev_domains = {"github.com","gitlab.com","dev.to","hackerrank.com","hashnode.com","keybase.io","npmjs.com"}
    prof_domains = {"about.me","linkedin.com","patreon.com","buymeacoffee.com","ko-fi.com"}
    name_map = {}
    for key, entry in intel.get("identity_clues",{}).items():
        if not key.startswith("name_"): continue
        raw = entry.get("value","")
        if not looks_like_real_name_v2(raw): continue
        domain = key.split("/")[0].replace("name_github","github.com").replace("name_generic_https://","")
        if domain not in name_map: name_map[domain] = {}
        if raw not in name_map[domain]: name_map[domain][raw] = 0
        name_map[domain][raw] += 1

    candidates = {}
    for domain, names in name_map.items():
        for name, cnt in names.items():
            if name not in candidates: candidates[name] = {"count":0,"platforms":set(),"dev":0,"prof":0,"email_match":False}
            candidates[name]["count"] += cnt
            candidates[name]["platforms"].add(domain)
            if domain in dev_domains: candidates[name]["dev"] += 1
            if domain in prof_domains: candidates[name]["prof"] += 1

    emails = intel.get("emails",{})
    for name, data in candidates.items():
        parts = name.lower().split()
        for email_key, email_entry in emails.items():
            local = email_entry["value"].split("@")[0].lower()
            if any(p in local for p in parts):
                data["email_match"] = True
                break

    scored = []
    for name, data in candidates.items():
        score = 0
        score += data["count"] * 10
        score += len(data["platforms"]) * 15
        score += data["dev"] * 20
        score += data["prof"] * 10
        if data["email_match"]: score += 25
        if len(name.split()) < 2: score -= 15
        if not data["dev"] and not data["prof"]: score -= 10
        score = max(0, min(100, score))
        scored.append({"name":name, "score":score, "platforms":len(data["platforms"]),
                       "breakdown":{"count":data["count"],"dev":data["dev"],"prof":data["prof"],"email_match":data["email_match"]}})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:5]

def run_name_analysis(name_list):
    res = {"name_origins":{}, "similarity_matrix":{}}
    if not name_list: return res
    try:
        from nametrace import NameTracer
        nt = NameTracer()
        preds = nt.predict(name_list, batch_size=len(name_list))
        for name,pred in zip(name_list, preds):
            res["name_origins"][name] = {"is_human":pred.get("is_human",False),"gender":pred.get("gender","unknown"),"subregion":pred.get("subregion","unknown")}
    except Exception as e: print(f"  NameTrace error: {e}")
    try:
        from rapidfuzz import fuzz
        for i,a in enumerate(name_list):
            for j,b in enumerate(name_list):
                if i>=j: continue
                score = fuzz.ratio(a.lower(), b.lower()) / 100.0
                if score>0.50: res["similarity_matrix"][f"{a} ↔ {b}"] = round(score,3)
    except Exception as e: print(f"  RapidFuzz error: {e}")
    return res

# -------------------------------------------------------------------
#  AI report generation (fully guarded)
# -------------------------------------------------------------------
def generate_ai_report(core, groq_api_key):
    """Generate an AI summary using Groq's Llama 3.3 model."""
    if not groq_api_key:
        print("  AI report skipped – no Groq API key set.")
        return None

    # Grab the intel dict safely
    if hasattr(core, 'intel'):
        intel = core.intel
    elif isinstance(core, dict):
        intel = core
    else:
        print(f"  AI report error: unexpected core type {type(core)}")
        return None

    try:
        from openai import OpenAI
        client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_api_key)

        # Defensive: confidence_scores might be a dict due to corrupted cache
        top_list = intel.get("confidence_scores", [])
        if isinstance(top_list, dict):
            # Convert dict to list of items (unlikely, but handle gracefully)
            top_list = [v for v in top_list.values() if isinstance(v, dict)]
        top_candidates = top_list[:3] if isinstance(top_list, list) else []

        email_list = []
        for key, entry in intel.get("emails", {}).items():
            if entry.get("source") != "email_guesser":
                email_list.append({"email": entry["value"], "source": entry["source"]})
        breach_status = {}
        for key, entry in intel.get("breaches", {}).items():
            breach_status[key] = "compromised" if "Not Compromised" not in str(entry["value"]) else "clean"
        profiles = [v["value"] for k, v in intel.get("social_profiles", {}).items() if v.get("value", "").startswith("http")][:15]

        summary = {
            "discord_username": intel.get("discord", {}).get("username", {}).get("value", "?"),
            "top_identities": [{"name": c["name"], "score": c["score"]} for c in top_candidates],
            "emails": email_list[:10],
            "breach_status": breach_status,
            "profile_urls": profiles
        }

        prompt = f"""You are an OSINT analyst. Based on the following data, produce a concise JSON report with keys: executive_summary, identity_assessment, digital_footprint, risk_indicators, next_steps.

Data: {json.dumps(summary, indent=2)}"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        raw = response.choices[0].message.content.strip()
        raw = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.MULTILINE)
        try:
            return json.loads(raw)
        except:
            return {"executive_summary": raw, "identity_assessment": "", "digital_footprint": "", "risk_indicators": "", "next_steps": ""}
    except Exception as e:
        import traceback
        print(f"  AI report error: {e}")
        traceback.print_exc()
        return None

def format_ai_report_markdown(report_dict):
    md = []
    def add_section(title, content):
        md.append(f"## {title}")
        md.append(str(content))
        md.append("")
    add_section("Executive Summary", report_dict.get("executive_summary",""))
    add_section("Identity Assessment", report_dict.get("identity_assessment",""))
    add_section("Digital Footprint", report_dict.get("digital_footprint",""))
    add_section("Risk Indicators", report_dict.get("risk_indicators",""))
    add_section("Recommended Next Steps", report_dict.get("next_steps",""))
    return "\n".join(md)

# -------------------------------------------------------------------
#  HTML report generation
# -------------------------------------------------------------------
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def generate_html_report(intel_core, target_id):
    if not os.path.exists(TEMPLATE_DIR):
        os.makedirs(TEMPLATE_DIR)

    template_path = os.path.join(TEMPLATE_DIR, "report.html")
    if not os.path.exists(template_path):
        _create_default_template(template_path)

    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(['html', 'xml'])
    )
    template = env.get_template("report.html")

    intel = intel_core.intel
    profiles = [{"key": k, "url": v.get("value","")} for k,v in intel.get("social_profiles",{}).items() if v.get("value","").startswith("http")][:50]
    emails = [{"email": v.get("value",""), "source": v.get("source","")} for v in intel.get("emails",{}).values()]
    top_names = intel.get("confidence_scores", [])
    if isinstance(top_names, dict):
        top_names = list(top_names.values())
    top_names = top_names[:5]

    html = template.render(
        target_id=target_id,
        timestamp=datetime.datetime.now().isoformat(),
        profiles=profiles,
        emails=emails,
        top_names=top_names,
        timeline=intel.get("timeline",[])
    )
    return html

def _create_default_template(path):
    default_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OSINT Report – {{ target_id }}</title>
<style>
  body { font-family: Arial, sans-serif; margin: 2em; background: #f4f4f4; }
  h1 { color: #2c3e50; }
  details { margin-bottom: 1em; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
  summary { padding: 1em; background: #3498db; color: white; border-radius: 8px; cursor: pointer; }
  summary:hover { background: #2980b9; }
  .content { padding: 1em; }
  ul { list-style: none; padding: 0; }
  li { margin-bottom: 0.5em; }
  a { color: #3498db; }
  .footer { margin-top: 2em; color: #7f8c8d; font-size: 0.9em; }
</style>
</head>
<body>
<h1>OSINT Investigation Report</h1>
<p><strong>Target ID:</strong> {{ target_id }}</p>
<p><strong>Generated:</strong> {{ timestamp }}</p>

<details open>
<summary>Discovered Profiles ({{ profiles|length }})</summary>
<div class="content">
  <ul>
    {% for p in profiles %}
    <li><a href="{{ p.url }}" target="_blank">{{ p.key }}</a></li>
    {% endfor %}
  </ul>
</div>
</details>

<details open>
<summary>Emails ({{ emails|length }})</summary>
<div class="content">
  <ul>
    {% for e in emails %}
    <li>{{ e.email }} (source: {{ e.source }})</li>
    {% endfor %}
  </ul>
</div>
</details>

<details>
<summary>Top Identity Candidates</summary>
<div class="content">
  <ul>
    {% for name in top_names %}
    <li>{{ name.name }} – score: {{ name.score }}</li>
    {% endfor %}
  </ul>
</div>
</details>

<details>
<summary>Timeline</summary>
<div class="content">
  <ul>
    {% for event in timeline %}
    <li>{{ event }}</li>
    {% endfor %}
  </ul>
</div>
</details>

<div class="footer">Generated by discord-osint pipeline</div>
</body>
</html>"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(default_html)
