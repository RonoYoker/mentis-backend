import http
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from onyx_proj.common.constants import *


class email_utility:

    def send_mail(self, tos: list, ccs: list, bccs: list, subject: str, body: str):
        try:
            message = MIMEMultipart()
            message['From'] = SMTP_FROM
            message['To'] = ",".join(tos)
            message['Cc'] = ",".join(ccs)
            message['Bcc'] = ",".join(bccs)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain; charset=utf-8'))
            session = smtplib.SMTP(SMTP_HOST, MAIL_SMTP_PORT)
            session.starttls()
            session.login(SMTP_USERNAME, SMTP_PASSWORD)
            session.send_message(message)
            session.quit()
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True)
