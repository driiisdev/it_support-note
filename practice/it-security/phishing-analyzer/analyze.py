"""
analyze.py - triage a suspicious email (.eml) the way a security analyst would, with a risk score.

Checks:
  headers   SPF / DKIM / DMARC results, From vs Reply-To vs Return-Path domains, display-name impersonation
  domains   look-alikes of your company / well-known brands (micros0ft, examp1e-corp, rn -> m ...)
  links     visible link text vs real destination, raw IP links, plain http, URL shorteners
  content   urgency/threat language, credential or payment requests, gift cards, secrecy
  files     risky attachment types (.html, .iso, .exe, .js, macros, double extensions)

Only reads the file - never opens links or attachments.

Usage:
    python analyze.py samples/01-credential-phish.eml
    python analyze.py samples/*.eml
    python analyze.py suspicious.eml --company example-corp.com
    (Outlook on the web / new Outlook: ... -> Save as/Download .eml  |  Gmail: More -> Download message.
     Classic desktop Outlook saves .msg, which this script does not read.)
"""

import argparse
import email
import glob
import ipaddress
import re
from email import policy
from email.utils import parseaddr
from html.parser import HTMLParser
from urllib.parse import urlparse

BRANDS = ["microsoft", "microsoftonline", "office365", "outlook", "google", "paypal", "apple",
          "amazon", "docusign", "dropbox", "linkedin", "dhl", "fedex", "netflix"]
SHORTENERS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", "buff.ly", "cutt.ly"}
RISKY_EXT = {".html", ".htm", ".iso", ".img", ".exe", ".scr", ".js", ".vbs", ".bat", ".cmd", ".ps1",
             ".lnk", ".hta", ".docm", ".xlsm", ".pptm", ".zip", ".rar", ".7z", ".one"}
URGENCY = [r"\burgent\b", r"immediately", r"within 24 hours", r"suspend", r"final notice", r"act now",
           r"as soon as possible", r"permanent(ly)? (loss|deleted|closed)", r"unusual (sign-in|activity)"]
ASKS = {"credentials": r"verify your (identity|account)|password|sign[- ]?in|log ?in to",
        "payment": r"wire transfer|bank details|invoice (is )?overdue|payment",
        "gift cards": r"gift ?cards?",
        "secrecy": r"confidential|don'?t (tell|mention)|keep this between"}
HOMOGLYPHS = [("0", "o"), ("1", "l"), ("rn", "m"), ("vv", "w"), ("3", "e"), ("5", "s")]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append(("".join(self._text).strip(), self._href))
            self._href = None


def domain_of(addr: str) -> str:
    return parseaddr(addr)[1].rpartition("@")[2].lower()


def registrable(host: str) -> str:
    """Rough 'base domain': last two labels (good enough here; real tools use the Public Suffix List)."""
    parts = host.lower().strip(".").split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else host


def normalize(s: str) -> str:
    for fake, real in HOMOGLYPHS:
        s = s.replace(fake, real)
    return s


def lookalike(domain: str, protected: list[str]) -> str | None:
    """Flag domains that become a protected name once look-alike characters are normalized."""
    label = registrable(domain).split(".")[0]
    for p in protected:
        p_label = p.split(".")[0]
        if label == p_label:
            continue  # it IS the real one (or same label, different TLD - handled elsewhere)
        if normalize(label) == p_label or (p_label in normalize(label) and label != p_label):
            return p
    return None


def analyze(path: str, company: str) -> None:
    with open(path, "rb") as f:
        msg = email.message_from_binary_file(f, policy=policy.default)

    findings: list[tuple[int, str]] = []  # (points, explanation)

    def flag(points: int, text: str):
        findings.append((points, text))

    from_hdr = msg.get("From", "")
    display, from_addr = parseaddr(from_hdr)
    from_dom = domain_of(from_hdr)
    reply_dom = domain_of(msg.get("Reply-To", "")) if msg.get("Reply-To") else None
    return_dom = domain_of(msg.get("Return-Path", "")) if msg.get("Return-Path") else None
    protected = [company] + BRANDS

    # --- Authentication results (added by YOUR mail server - the most trustworthy header)
    auth = " ".join(str(h) for h in msg.get_all("Authentication-Results", []))
    for mech in ("spf", "dkim", "dmarc"):
        m = re.search(rf"{mech}=(\w+)", auth)
        result = m.group(1) if m else "missing"
        if result in ("fail", "softfail", "none", "missing", "permerror"):
            flag(3 if mech == "dmarc" else 2, f"{mech.upper()} = {result} - sender not verified for {from_dom}")

    # --- Sender identity
    if reply_dom and registrable(reply_dom) != registrable(from_dom):
        flag(3, f"Reply-To goes to {reply_dom}, not the sender's domain {from_dom} - replies go to someone else")
    if return_dom and registrable(return_dom) != registrable(from_dom):
        flag(1, f"Return-Path domain {return_dom} differs from From domain {from_dom}")
    if (hit := lookalike(from_dom, protected)):
        flag(4, f"From domain {from_dom} looks like '{hit}' with swapped characters (look-alike domain)")
    for brand in BRANDS + [company.split(".")[0]]:
        if brand in display.lower().replace(" ", "") and brand not in from_dom.replace("-", ""):
            flag(3, f"Display name '{display}' claims to be {brand} but the address is {from_addr}")
            break
    if re.search(r"\b(ceo|cfo|director|president)\b", display, re.I) and registrable(from_dom) != company:
        flag(4, f"Display name '{display}' claims an executive role but sends from external {from_dom} (CEO fraud)")

    # --- Body + links
    body_parts, attachments = [], []
    for part in msg.walk():
        if part.is_attachment():
            attachments.append(part.get_filename() or "unnamed")
        elif part.get_content_type() in ("text/plain", "text/html"):
            body_parts.append((part.get_content_type(), part.get_content()))
    text = " ".join(re.sub(r"<[^>]+>", " ", b) for _, b in body_parts)

    links = []
    for ctype, b in body_parts:
        if ctype == "text/html":
            lp = LinkParser()
            lp.feed(b)
            links += lp.links
        else:
            links += [(u, u) for u in re.findall(r"https?://\S+", b)]
    for visible, href in links:
        host = (urlparse(href).hostname or "").lower()
        vis_host = (urlparse(visible).hostname or "").lower() if visible.startswith("http") else None
        if vis_host and registrable(vis_host) != registrable(host):
            flag(4, f"Link text shows {vis_host} but actually goes to {host}")
        if href.startswith("http://"):
            flag(1, f"Link uses unencrypted http: {href[:60]}")
        try:
            ipaddress.ip_address(host)
            flag(3, f"Link points to a raw IP address: {host}")
        except ValueError:
            pass
        if host in SHORTENERS:
            flag(2, f"Link uses a URL shortener ({host}) - destination hidden")
        if (hit := lookalike(host, protected)):
            flag(3, f"Link domain {host} imitates '{hit}'")

    # --- Language
    urgency_hits = [p for p in URGENCY if re.search(p, text, re.I)]
    if urgency_hits:
        flag(min(3, len(urgency_hits)), f"Urgency/threat language ({len(urgency_hits)} phrases) - pressure to act before thinking")
    for label, pattern in ASKS.items():
        if re.search(pattern, text, re.I):
            flag(3 if label in ("gift cards", "credentials") else 2, f"Asks for {label}")

    # --- Attachments
    for name in attachments:
        lower = name.lower()
        ext = "." + lower.rsplit(".", 1)[-1] if "." in lower else ""
        if re.search(r"\.\w{2,4}\.(exe|scr|js|vbs|bat|cmd|lnk|hta)$", lower):
            flag(5, f"Attachment '{name}' uses a double extension to hide that it's a program")
        elif ext in RISKY_EXT:
            flag(3, f"Risky attachment type: {name} ({ext} files can run code or host fake login pages)")

    score = sum(p for p, _ in findings)
    verdict = ("HIGH RISK - report as phishing, do not click/reply" if score >= 10 else
               "SUSPICIOUS - verify with the sender through another channel" if score >= 4 else
               "LOW RISK - no strong phishing signals (still use judgment)")
    print(f"\n{path}")
    print(f"  From    : {from_hdr}")
    print(f"  Subject : {msg.get('Subject', '')}")
    print(f"  Links   : {len(links)}   Attachments: {', '.join(attachments) or 'none'}")
    for points, text_ in sorted(findings, reverse=True):
        print(f"   +{points}  {text_}")
    print(f"  SCORE {score} -> {verdict}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("files", nargs="+")
    p.add_argument("--company", default="example-corp.com", help="your organization's email domain")
    args = p.parse_args()
    for pattern in args.files:
        for path in sorted(glob.glob(pattern)) or [pattern]:
            analyze(path, args.company.lower())


if __name__ == "__main__":
    main()
