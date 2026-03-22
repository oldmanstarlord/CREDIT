"""
Notification Service for email and SMS
Handles application status updates, approval/rejection notifications
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending email and SMS notifications"""

    def __init__(self):
        self.email_enabled = bool(settings.SMTP_HOST and settings.SMTP_USER)
        self.sms_enabled = False  # SMS provider not configured yet
        
        if self.email_enabled:
            logger.info("Email notifications enabled")
        else:
            logger.warning("Email notifications disabled - SMTP not configured")

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ) -> bool:
        """
        Send email notification
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML email body
            body_text: Plain text fallback
            
        Returns:
            bool indicating success
        """
        if not self.email_enabled:
            logger.warning(f"Email not sent (disabled): {subject} to {to_email}")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg['To'] = to_email

            # Add plain text version
            if body_text:
                part1 = MIMEText(body_text, 'plain')
                msg.attach(part1)

            # Add HTML version
            part2 = MIMEText(body_html, 'html')
            msg.attach(part2)

            # Send email
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT or 587) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False

    def send_application_submitted(
        self,
        user_email: str,
        user_name: str,
        application_number: str,
        requested_amount: float
    ) -> bool:
        """Send notification when application is submitted"""
        
        subject = f"Application Received - {application_number}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #00AEEF;">Application Received</h2>
                <p>Dear {user_name},</p>
                <p>Thank you for applying for a loan with Barclays Credit Intelligence Platform.</p>
                
                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Application Number:</strong> {application_number}</p>
                    <p><strong>Requested Amount:</strong> ₹{requested_amount:,.2f}</p>
                    <p><strong>Status:</strong> Under Review</p>
                </div>
                
                <p>Your application is being processed. You will receive an update within 24-48 hours.</p>
                <p>You can track your application status anytime by logging into your account.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>Barclays Credit Team</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Application Received
        
        Dear {user_name},
        
        Thank you for applying for a loan with Barclays Credit Intelligence Platform.
        
        Application Number: {application_number}
        Requested Amount: ₹{requested_amount:,.2f}
        Status: Under Review
        
        Your application is being processed. You will receive an update within 24-48 hours.
        
        Best regards,
        Barclays Credit Team
        """
        
        return self.send_email(user_email, subject, body_html, body_text)

    def send_application_approved(
        self,
        user_email: str,
        user_name: str,
        application_number: str,
        approved_amount: float,
        interest_rate: float,
        tenure_months: int
    ) -> bool:
        """Send notification when application is approved"""
        
        subject = f"Loan Approved - {application_number}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #10B981;">🎉 Congratulations! Your Loan is Approved</h2>
                <p>Dear {user_name},</p>
                <p>We are pleased to inform you that your loan application has been approved.</p>
                
                <div style="background-color: #D1FAE5; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #10B981;">
                    <p><strong>Application Number:</strong> {application_number}</p>
                    <p><strong>Approved Amount:</strong> ₹{approved_amount:,.2f}</p>
                    <p><strong>Interest Rate:</strong> {interest_rate}% per annum</p>
                    <p><strong>Tenure:</strong> {tenure_months} months</p>
                </div>
                
                <h3>Next Steps:</h3>
                <ol>
                    <li>Complete KYC verification (if pending)</li>
                    <li>Submit required documents</li>
                    <li>Sign loan agreement</li>
                    <li>Funds will be disbursed within 2-3 business days</li>
                </ol>
                
                <p>Please log in to your account to proceed with the next steps.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>Barclays Credit Team</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Congratulations! Your Loan is Approved
        
        Dear {user_name},
        
        We are pleased to inform you that your loan application has been approved.
        
        Application Number: {application_number}
        Approved Amount: ₹{approved_amount:,.2f}
        Interest Rate: {interest_rate}% per annum
        Tenure: {tenure_months} months
        
        Next Steps:
        1. Complete KYC verification (if pending)
        2. Submit required documents
        3. Sign loan agreement
        4. Funds will be disbursed within 2-3 business days
        
        Please log in to your account to proceed.
        
        Best regards,
        Barclays Credit Team
        """
        
        return self.send_email(user_email, subject, body_html, body_text)

    def send_application_rejected(
        self,
        user_email: str,
        user_name: str,
        application_number: str,
        reason: str
    ) -> bool:
        """Send notification when application is rejected"""
        
        subject = f"Application Update - {application_number}"
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #EF4444;">Application Decision</h2>
                <p>Dear {user_name},</p>
                <p>Thank you for your interest in Barclays Credit Intelligence Platform.</p>
                
                <div style="background-color: #FEE2E2; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #EF4444;">
                    <p><strong>Application Number:</strong> {application_number}</p>
                    <p><strong>Status:</strong> Not Approved</p>
                    <p><strong>Reason:</strong> {reason}</p>
                </div>
                
                <p>We understand this may be disappointing. Here are some steps you can take:</p>
                <ul>
                    <li>Review your credit profile and address any issues</li>
                    <li>Reduce existing debt obligations</li>
                    <li>Build a stronger credit history</li>
                    <li>You may reapply after 90 days</li>
                </ul>
                
                <p>If you believe this decision was made in error, you have the right to appeal within 30 days.</p>
                
                <p style="margin-top: 30px;">Best regards,<br>Barclays Credit Team</p>
            </div>
        </body>
        </html>
        """
        
        body_text = f"""
        Application Decision
        
        Dear {user_name},
        
        Thank you for your interest in Barclays Credit Intelligence Platform.
        
        Application Number: {application_number}
        Status: Not Approved
        Reason: {reason}
        
        We understand this may be disappointing. Here are some steps you can take:
        - Review your credit profile and address any issues
        - Reduce existing debt obligations
        - Build a stronger credit history
        - You may reapply after 90 days
        
        If you believe this decision was made in error, you have the right to appeal within 30 days.
        
        Best regards,
        Barclays Credit Team
        """
        
        return self.send_email(user_email, subject, body_html, body_text)

    def send_sms(self, phone_number: str, message: str) -> bool:
        """
        Send SMS notification (placeholder - requires SMS provider integration)
        
        Args:
            phone_number: Recipient phone number
            message: SMS message text
            
        Returns:
            bool indicating success
        """
        if not self.sms_enabled:
            logger.warning(f"SMS not sent (disabled): {message[:50]}... to {phone_number}")
            return False

        # TODO: Integrate with SMS provider (Twilio, AWS SNS, etc.)
        logger.info(f"SMS would be sent to {phone_number}: {message}")
        return False

    def send_application_status_sms(
        self,
        phone_number: str,
        application_number: str,
        status: str
    ) -> bool:
        """Send SMS notification for application status update"""
        
        message = f"Barclays: Your loan application {application_number} status: {status}. Check your email for details."
        return self.send_sms(phone_number, message)
