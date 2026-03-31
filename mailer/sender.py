import smtplib
from email.mime.text import MIMEText
from config import SMTP_EMAIL, SMTP_PASSWORD


def generate_subject(offer):

    if offer == "feedback":
        return "Quick thought about your customer feedback"
    elif offer == "chatbot":
        return "Quick idea for your support flow"
    elif offer == "dashboard":
        return "Small idea about your data"

    return "Quick idea"


def send_email(to_email, body, tracking_id, subject):

    tracking_pixel = f'<img src="https://yourdomain.com/open?id={tracking_id}" width="1" height="1"/>'

    msg = MIMEText(body + tracking_pixel, "html")
    msg["Subject"] = subject
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