import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from src.config import Config
from src.database import log_outreach

class OutreachSender:
    def send_email_outreach(self, profile: dict) -> str:
        channel_id = profile["channel_id"]
        email = profile["email"]
        current_status = profile.get("outreach_status", "Pending")

        if "Sent" in str(current_status):
            return "Skipped (Duplicate Prevention)"

        if not email or email == "Not Found":
            status = "Manual DM Queue (Email Not Found)"
            log_outreach(channel_id, status)
            return status

        if Config.DRY_RUN_SEND:
            status = "Sent (Simulated Dry-Run)"
            log_outreach(channel_id, status)
            return status

        try:
            msg = MIMEMultipart()
            msg["From"] = Config.SMTP_EMAIL
            msg["To"] = email
            msg["Subject"] = profile["email_subject"]
            msg.attach(MIMEText(profile["email_pitch"], "plain"))

            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_EMAIL, Config.SMTP_APP_PASSWORD)
                server.send_message(msg)

            status = "Sent (Live SMTP)"
            log_outreach(channel_id, status)
            return status
        except Exception as e:
            status = f"Failed ({str(e)[:40]})"
            log_outreach(channel_id, status)
            return status
