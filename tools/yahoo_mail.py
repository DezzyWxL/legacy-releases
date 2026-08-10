#!/usr/bin/env python3
"""
Yahoo Mail Assistant — single-file, no-install email helper.

Lets you read, search, and reply to Yahoo Mail from any computer with Python 3
(Windows, Mac, or Linux). Pure standard library — no pip installs required.

USAGE (Windows):
  1. Make sure Python 3 is installed (https://python.org/downloads — check
     "Add python.exe to PATH" during install).
  2. Download this file (yahoo_mail.py).
  3. Double-click it, OR open a terminal and run:
        python yahoo_mail.py
  4. First run signs you in (email + app password) and saves it to
     yahoo_mail_credentials.json next to this file.

WHAT YOU NEED FIRST — a Yahoo APP PASSWORD (not your login password):
  1. Sign in to Yahoo Mail in a browser.
  2. Go to Account Security:  https://login.yahoo.com/account/security
  3. Under "App passwords", generate one (it looks like:  abcd efgh ijkl mnop)
  4. Use that 16-char code here. Your normal login password will NOT work.

MENU:
  1. Read newest emails      — shows the latest messages in your inbox
  2. Search emails           — search by sender or subject
  3. Read one email          — full body of a specific message
  4. Send an email           — compose and send a new message
  5. Reply to an email       — reply to a message you've read
  6. Change account          — switch to a different Yahoo account
  7. Quit
"""

import getpass
import imaplib
import json
import os
import smtplib
import sys
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Yahoo servers
IMAP_HOST = "imap.mail.yahoo.com"
IMAP_PORT = 993
SMTP_HOST = "smtp.mail.yahoo.com"
SMTP_PORT = 465

# Credentials live next to this file
CRED_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yahoo_mail_credentials.json")


# ── helpers ────────────────────────────────────────────────────────────────
def load_creds():
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return None


def save_creds(email, app_password):
    with open(CRED_FILE, "w") as f:
        json.dump({"email": email, "app_password": app_password}, f, indent=2)
    try:
        os.chmod(CRED_FILE, 0o600)
    except Exception:
        pass
    print(f"  ✓ Saved sign-in for {email}")


def sign_in():
    """Prompt for email + app password, validate against Yahoo, save if good."""
    print("\n── Yahoo Sign-In ──")
    print("  (Need an app password? Generate one at:")
    print("   https://login.yahoo.com/account/security → App passwords)")
    email = input("  Yahoo email: ").strip()
    if not email:
        print("  No email entered.")
        return None
    app_password = ""
    try:
        app_password = getpass.getpass("  App password: ").strip()
    except Exception:
        # Non-TTY fallback (piped input / unusual terminals): just read a line.
        app_password = input("  App password: ").strip()
    if not app_password:
        print("  No app password entered.")
        return None

    print("  Validating against Yahoo…")
    try:
        conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        conn.login(email, app_password)
        conn.select("INBOX")
        conn.logout()
    except imaplib.IMAP4.error as e:
        print(f"  ✗ Sign-in failed: {e}")
        if "AUTHENTICATIONFAILED" in str(e):
            print("    That email/password was rejected. Make sure you're using an")
            print("    APP PASSWORD (16 chars), not your normal login password.")
        return None
    except Exception as e:
        print(f"  ✗ Could not reach Yahoo: {e}")
        return None

    save_creds(email, app_password)
    return {"email": email, "app_password": app_password}


def get_creds():
    creds = load_creds()
    if creds:
        return creds
    return sign_in()


def connect_imap(creds):
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(creds["email"], creds["app_password"])
    conn.select("INBOX")
    return conn


def decode(value):
    if not value:
        return ""
    parts = decode_header(value)
    out = []
    for text, charset in parts:
        if isinstance(text, bytes):
            out.append(text.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(text)
    return "".join(out)


def body_text(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    continue
        for part in msg.walk():
            if part.get_content_type().startswith("text/"):
                try:
                    return part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    continue
    else:
        try:
            return msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
        except Exception:
            return str(msg.get_payload())
    return ""


def fetch_list(conn, uids):
    out = []
    for uid in uids:
        typ, data = conn.fetch(uid, "(RFC822)")
        if typ != "OK":
            continue
        msg = __import__("email").message_from_bytes(data[0][1])
        out.append({
            "uid": uid.decode(),
            "from": decode(msg.get("From", "")),
            "subject": decode(msg.get("Subject", "(No Subject)")),
            "date": msg.get("Date", ""),
        })
    return out


# ── menu actions ───────────────────────────────────────────────────────────
def read_newest(creds):
    conn = connect_imap(creds)
    try:
        typ, data = conn.search(None, "ALL")
        uids = data[0].split()[::-1][:10]
        msgs = fetch_list(conn, uids)
        print(f"\n── Newest {len(msgs)} emails in your inbox ──")
        for i, m in enumerate(msgs, 1):
            print(f"  {i}. [{m['uid']}] {m['from']}")
            print(f"       {m['subject']}")
            print(f"       {m['date']}")
        return msgs
    finally:
        conn.logout()


def search(creds):
    conn = connect_imap(creds)
    try:
        term = input("  Search for (sender or subject text): ").strip()
        if not term:
            print("  No search term.")
            return []
        typ, data = conn.search(None, f'FROM "{term}"')
        if typ != "OK" or not data[0]:
            typ, data = conn.search(None, f'SUBJECT "{term}"')
        uids = data[0].split()[::-1][:10]
        msgs = fetch_list(conn, uids)
        print(f"\n── {len(msgs)} matches for '{term}' ──")
        for i, m in enumerate(msgs, 1):
            print(f"  {i}. [{m['uid']}] {m['from']}")
            print(f"       {m['subject']}")
        return msgs
    finally:
        conn.logout()


def read_one(creds):
    uid = input("  Message UID (from the list above): ").strip()
    if not uid:
        return
    conn = connect_imap(creds)
    try:
        typ, data = conn.fetch(uid.encode(), "(RFC822)")
        if typ != "OK":
            print("  Could not fetch that message.")
            return
        msg = __import__("email").message_from_bytes(data[0][1])
        print("\n── Message ──")
        print(f"  From:    {decode(msg.get('From', ''))}")
        print(f"  To:      {decode(msg.get('To', ''))}")
        print(f"  Subject: {decode(msg.get('Subject', '(No Subject)'))}")
        print(f"  Date:    {msg.get('Date', '')}")
        print("\n  Body:")
        print(body_text(msg))
        print("\n  ──────────────")
        return msg
    finally:
        conn.logout()


def send(creds, reply_to=None, reply_subject=None):
    to = input("  To (email): ").strip()
    if not to:
        print("  No recipient.")
        return
    subject = reply_subject or input("  Subject: ").strip()
    print("  Body (type your message, then press Enter twice on a blank line):")
    lines = []
    while True:
        line = input()
        if line == "" and lines and lines[-1] == "":
            break
        lines.append(line)
    body = "\n".join(lines).strip()

    msg = MIMEText(body)
    msg["From"] = creds["email"]
    msg["To"] = to
    msg["Subject"] = subject
    if reply_to:
        msg["References"] = reply_to.get("Message-ID", "")

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(creds["email"], creds["app_password"])
            server.sendmail(creds["email"], [to], msg.as_string())
        print(f"  ✓ Sent to {to}")
    except Exception as e:
        print(f"  ✗ Send failed: {e}")


def reply(creds):
    uid = input("  Message UID to reply to: ").strip()
    if not uid:
        return
    conn = connect_imap(creds)
    try:
        typ, data = conn.fetch(uid.encode(), "(RFC822)")
        if typ != "OK":
            print("  Could not fetch that message.")
            return
        msg = __import__("email").message_from_bytes(data[0][1])
        from_addr = decode(msg.get("From", ""))
        subject = decode(msg.get("Subject", "(No Subject)"))
        if not subject.lower().startswith("re:"):
            subject = "Re: " + subject
        print(f"  Replying to: {from_addr}")
        print(f"  Subject:     {subject}")
        send(creds, reply_to=msg, reply_subject=subject)
    finally:
        conn.logout()


# ── main ───────────────────────────────────────────────────────────────────
def main():
    print("=" * 50)
    print("  YAHOO MAIL ASSISTANT")
    print("  Read, search, and reply to Yahoo Mail")
    print("=" * 50)

    creds = get_creds()
    if not creds:
        print("  Could not sign in. Exiting.")
        return

    while True:
        print(f"\n  Signed in as: {creds['email']}")
        print("  ─────────────────────────────")
        print("  1. Read newest emails")
        print("  2. Search emails")
        print("  3. Read one email")
        print("  4. Send an email")
        print("  5. Reply to an email")
        print("  6. Change account")
        print("  7. Quit")
        choice = input("  Choose [1-7]: ").strip()

        if choice == "1":
            read_newest(creds)
        elif choice == "2":
            search(creds)
        elif choice == "3":
            read_one(creds)
        elif choice == "4":
            send(creds)
        elif choice == "5":
            reply(creds)
        elif choice == "6":
            creds = sign_in()
            if not creds:
                print("  Sign-in cancelled; keeping current account.")
                creds = load_creds()
        elif choice == "7":
            print("  Goodbye!")
            return
        else:
            print("  Invalid choice.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n  Exiting.")
        sys.exit(0)
