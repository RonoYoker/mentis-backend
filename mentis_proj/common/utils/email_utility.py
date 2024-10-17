import http
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mentis_proj.common.constants import *

from email import encoders
from email.mime.base import MIMEBase


class email_utility:

    def send_mail(self, tos: list, ccs: list, bccs: list, subject: str, body: str, file_path=None, file_name=None):
        try:
            message = MIMEMultipart()
            message['From'] = SMTP_FROM
            message['To'] = ",".join(tos)
            message['Cc'] = ",".join(ccs)
            message['Bcc'] = ",".join(bccs)
            message['Subject'] = subject
            message.attach(MIMEText(body, 'plain; charset=utf-8'))
            if file_path is not None and file_name is not None:
                with open(file_path, "rb") as attachment:
                    # Create a MIMEBase object for the attachment
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                # Encode the attachment
                encoders.encode_base64(part)

                # Add the header to specify the attachment's filename
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={file_name}",
                )

                # Attach the file to the message
                message.attach(part)
            session = smtplib.SMTP(SMTP_HOST, MAIL_SMTP_PORT)
            session.starttls()
            session.login(SMTP_USERNAME, SMTP_PASSWORD)
            session.send_message(message)
            session.quit()
        except Exception as ex:
            return dict(status=False, message=str(ex))
        return dict(status=True)
