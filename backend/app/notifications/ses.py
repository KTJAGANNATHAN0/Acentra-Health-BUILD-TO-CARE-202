"""AWS Simple Email Service (SES) Notifier."""
import logging
from typing import List, Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.notifications.base import Notifier, AlertPayload

logger = logging.getLogger(__name__)


class SESNotifier(Notifier):
    """Sends rich HTML & plain text fraud alerts via AWS SES."""

    def __init__(
        self,
        sender: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        region: Optional[str] = None
    ):
        self.sender = sender or settings.SES_SENDER
        self.recipients = recipients or settings.SES_RECIPIENTS
        self.region = region or settings.AWS_REGION
        self._client = None

    def _get_client(self):
        if self._client is None:
            kwargs = {"region_name": self.region}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self._client = boto3.client("ses", **kwargs)
        return self._client

    def send_alert(self, payload: AlertPayload) -> bool:
        if not self.sender or not self.recipients:
            logger.error("SES alert cannot be sent: SES_SENDER or SES_RECIPIENTS is not configured")
            return False

        subject = f"[HIGH RISK ALERT] Score {payload.score} - Transaction {payload.transaction_id[:8]}"
        
        rules_html = "".join(
            f"<li><strong>{rule}:</strong> {reason}</li>"
            for rule, reason in zip(payload.triggered_rules, payload.rule_reasons)
        )
        
        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin-bottom: 20px;">
                <h2 style="color: #b91c1c; margin-top: 0;">High Risk Fraud Alert Detected</h2>
                <p style="margin: 0; font-size: 16px;">
                    Risk Score: <strong style="color: #b91c1c; font-size: 20px;">{payload.score}/100</strong>
                </p>
            </div>
            
            <h3>Transaction Details</h3>
            <table style="border-collapse: collapse; width: 100%; max-width: 600px;">
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Transaction ID:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{payload.transaction_id}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Account ID:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{payload.account_id}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Amount:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{payload.amount:.2f} {payload.currency}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Merchant:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{payload.merchant}</td></tr>
                <tr><td style="padding: 8px; border-bottom: 1px solid #ddd;"><strong>Timestamp:</strong></td><td style="padding: 8px; border-bottom: 1px solid #ddd;">{payload.timestamp.isoformat()}</td></tr>
            </table>

            <h3>Triggered Fraud Rules</h3>
            <ul>{rules_html}</ul>

            <div style="margin-top: 30px;">
                <a href="{payload.console_link}" style="background-color: #dc2626; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                    Investigate in Reviewer Console
                </a>
            </div>
        </body>
        </html>
        """

        body_text = f"""
HIGH RISK FRAUD ALERT
Risk Score: {payload.score}/100
Transaction ID: {payload.transaction_id}
Account ID: {payload.account_id}
Amount: {payload.amount:.2f} {payload.currency}
Merchant: {payload.merchant}
Triggered Rules: {', '.join(payload.triggered_rules)}

Console link: {payload.console_link}
        """

        try:
            client = self._get_client()
            client.send_email(
                Source=self.sender,
                Destination={"ToAddresses": self.recipients},
                Message={
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {
                        "Html": {"Data": body_html, "Charset": "UTF-8"},
                        "Text": {"Data": body_text, "Charset": "UTF-8"}
                    }
                }
            )
            logger.info(f"SES email alert successfully sent to {self.recipients}")
            return True
        except (BotoCoreError, ClientError) as ex:
            logger.error(f"Failed to send email via SES: {ex}")
            return False
