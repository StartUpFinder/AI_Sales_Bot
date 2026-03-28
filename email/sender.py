import smtplib
from email.mime.text import MIMEText
from config import SMTP_EMAIL, SMTP_PASSWORD


def send_email(to_email, body):

    msg = MIMEText(body, "html")
    msg["Subject"] = "Quick idea for your business"
    msg["From"] = SMTP_EMAIL
    msg["To"] = to_email

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        print("Email error:", e)
        return False