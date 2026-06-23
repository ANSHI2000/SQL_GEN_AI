
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp-relay.brevo.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("EMAIL_FROM", self.smtp_user)
        
        logger.info(f"Email service initialized with host: {self.smtp_host}")
    
    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Email failed: {e}")
            return False
    
    def send_otp_email(self, to_email: str, otp_code: str) -> bool:
        subject = "🔐 Your OTP Code for SQL Genie"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background: #4CAF50; padding: 20px; color: white; text-align: center;">
                <h1>SQL Genie</h1>
                <p>NLP to SQL Query Generator</p>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <h2>Your Verification Code</h2>
                <div style="background: #f5f5f5; padding: 20px; font-size: 32px; text-align: center; letter-spacing: 8px;">
                    <strong>{otp_code}</strong>
                </div>
                <p>This code expires in <strong>5 minutes</strong>.</p>
                <p style="color: #666; font-size: 12px;">If you didn't request this, ignore this email.</p>
            </div>
        </body>
        </html>
        """
        return self.send_email(to_email, subject, body)

email_service = EmailService()

def send_otp_email(to_email: str, otp_code: str, name: str = "") -> bool:
    """Module-level function for sending OTP emails (called by auth routes)"""
    return email_service.send_otp_email(to_email, otp_code)
