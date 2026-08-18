import imaplib
import email
from email.header import decode_header
import json
import os

SKILL_INFO = {
    "name": "email_assistant",
    "description": "Gelen kutusundaki son e-postaları okur, Türkçe özet çıkarır ve aksiyon adımları belirler.",
    "version": "1.0.0"
}

def decode_str(header_value):
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    header_str = ""
    for text, encoding in decoded_list:
        if isinstance(text, bytes):
            header_str += text.decode(encoding or "utf-8", errors="ignore")
        else:
            header_str += text
    return header_str

def fetch_latest_emails(server="imap.gmail.com", port=993, email_address="", password="", limit=3):
    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(email_address, password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")
        mail_ids = messages[0].split()

        if not mail_ids:
            status, messages = mail.search(None, "ALL")
            mail_ids = messages[0].split()

        latest_ids = mail_ids[-limit:]
        email_list = []

        for m_id in reversed(latest_ids):
            res, msg_data = mail.fetch(m_id, "(RFC822)")
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    subject = decode_str(msg["Subject"])
                    from_str = decode_str(msg["From"])

                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                    email_list.append({
                        "kimden": from_str,
                        "konu": subject,
                        "icerik": body[:1500]
                    })

        mail.logout()
        return email_list
    except Exception as e:
        return {"hata": f"E-posta bağlantı/okuma hatası: {str(e)}"}

def run_skill(model_runner, config_path=None):
    if not config_path:
        config_path = os.path.join(os.path.dirname(__file__), "config.json")
    
    if not os.path.exists(config_path):
        return "⚠️ config.json dosyası bulunamadı. Lütfen e-posta ayarlarınızı yapın."

    with open(config_path, "r", encoding="utf-8") as f:
        email_config = json.load(f)

    if not email_config.get("email") or email_config.get("email") == "ornek@gmail.com":
        return "⚠️ Lütfen skills/email_assistant/config.json dosyasına geçerli e-posta ve uygulama şifrenizi girin."

    emails = fetch_latest_emails(
        server=email_config.get("server", "imap.gmail.com"),
        email_address=email_config.get("email"),
        password=email_config.get("password"),
        limit=email_config.get("limit", 3)
    )

    if isinstance(emails, dict) and "hata" in emails:
        return emails["hata"]

    if not emails:
        return "📭 İşlenecek e-posta bulunamadı."

    prompt = f"""Aşağıdaki e-postaları analiz et. Her e-posta için:
1. Gönderen ve Konu
2. 2-3 cümlelik Türkçe Özeti
3. Alınması gereken bir aksiyon var mı? (Varsa kısa not yaz)

E-Postalar:
{json.dumps(emails, ensure_ascii=False, indent=2)}
"""
    return model_runner(prompt)
