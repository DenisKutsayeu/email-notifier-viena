import imaplib
import asyncio
import email
from email.header import decode_header
from email.utils import parseaddr
import requests
import html
import aiogram
import aiohttp
from loguru import logger
import config


bot = aiogram.Bot(token=config.TELEGRAM_BOT_TOKEN)


def refresh_access_token():
    """Обновляет Access Token с помощью Refresh Token."""
    data = {
        "client_id": config.CLIENT_ID,
        "client_secret": config.CLIENT_SECRET,
        "refresh_token": config.REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }

    response = requests.post(config.TOKEN_URL, data=data)
    if response.status_code == 200:
        new_token = response.json()["access_token"]
        logger.info("✅ Access Token обновлен")
        return new_token
    else:
        logger.error("❌ Ошибка обновления токена:", response.text)
        return None


def connect_to_mailbox():
    """Подключается к Gmail через IMAP с OAuth2."""
    access_token = refresh_access_token()
    if not access_token:
        return None

    auth_string = f"user={config.EMAIL_LOGIN}\x01auth=Bearer {access_token}\x01\x01"

    try:
        mail = imaplib.IMAP4_SSL(config.IMAP_SERVER, config.IMAP_PORT)
        mail.authenticate("XOAUTH2", lambda _: auth_string)
        mail.select("inbox")
        return mail
    except imaplib.IMAP4.error:
        logger.error("❌ Ошибка аутентификации в IMAP. Проверьте токен.")
        return None


def fetch_unread_emails():
    """Ищет непрочитанные письма от нужного отправителя."""
    mail = connect_to_mailbox()
    if not mail:
        return []

    status, messages = mail.search(None, f'(UNSEEN FROM "{config.SENDER_EMAIL}")')

    if status != "OK":
        logger.error("Ошибка поиска писем.")
        return []

    email_ids = messages[0].split()
    unread_emails = []

    for email_id in email_ids:
        status, msg_data = mail.fetch(email_id, "(RFC822)")
        if status != "OK":
            continue

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])

                subject, encoding = decode_header(msg["Subject"])[0]
                subject = subject.decode(encoding or "utf-8") if isinstance(subject, bytes) else subject

                from_email = msg.get("From")
                sender_name, sender_email = parseaddr(from_email)

                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                            break
                else:
                    body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

                unread_emails.append({"subject": subject, "from": sender_email, "body": body[:500]})

        mail.store(email_id, "+FLAGS", "\\Seen")

    mail.close()
    mail.logout()
    return unread_emails


async def send_telegram_message(text):
    """Отправляет уведомление в Telegram."""
    async with aiohttp.ClientSession() as session:
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        safe_text = html.escape(text)

        payload = {"chat_id": config.TELEGRAM_CHAT_ID, "text": safe_text, "parse_mode": "HTML"}
        async with session.post(url, json=payload) as resp:
            if resp.status != 200:
                logger.error(f"Ошибка при отправке в Telegram: {await resp.text()}")


async def check_new_emails():
    """Основная функция, проверяет новые письма и отправляет уведомления."""
    unread_emails = fetch_unread_emails()
    if not unread_emails:
        logger.info("Нет новых писем.")
        return

    for email_data in unread_emails:
        text = (
            f"📩 Новое письмо от {html.escape(email_data['from'])}\n"
            f" Тема: {html.escape(email_data['subject'])}\n\n"
            f" Текст: {html.escape(email_data['body'])}"
        )
        await send_telegram_message(text)


if __name__ == "__main__":
    asyncio.run(check_new_emails())
