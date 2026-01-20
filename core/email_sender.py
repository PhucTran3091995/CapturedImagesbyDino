import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os

class EmailSender:
    def __init__(self, smtp_server="smtp.gmail.com", smtp_port=587, sender_email="", password=""):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.password = password

    def send_email(self, recipient_email, subject, body, attachment_path=None):
        """
        Sends an email with an optional attachment.
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain'))

            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )
                msg.attach(part)

            # Connect to server
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls() # Secure the connection
            server.login(self.sender_email, self.password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()
            return True, "Email sent successfully!"

        except Exception as e:
            return False, str(e)
