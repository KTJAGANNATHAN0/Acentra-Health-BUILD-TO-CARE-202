"""AWS Simple Notification Service (SNS) Notifier."""
import json
import logging
from typing import Optional
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings
from app.notifications.base import Notifier, AlertPayload

logger = logging.getLogger(__name__)


class SNSNotifier(Notifier):
    """Publishes structured JSON alerts to an AWS SNS Topic."""

    def __init__(self, topic_arn: Optional[str] = None, region: Optional[str] = None):
        self.topic_arn = topic_arn or settings.SNS_TOPIC_ARN
        self.region = region or settings.AWS_REGION
        self._client = None

    def _get_client(self):
        if self._client is None:
            kwargs = {"region_name": self.region}
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
                kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
            self._client = boto3.client("sns", **kwargs)
        return self._client

    def send_alert(self, payload: AlertPayload) -> bool:
        if not self.topic_arn:
            logger.error("SNS alert cannot be sent: SNS_TOPIC_ARN is not configured")
            return False

        message = {
            "version": "1.0",
            "source": "fraud-rule-engine",
            "event": "HIGH_RISK_FRAUD_DETECTED",
            "transaction_id": payload.transaction_id,
            "flag_id": payload.flag_id,
            "account_id": payload.account_id,
            "amount": payload.amount,
            "currency": payload.currency,
            "merchant": payload.merchant,
            "risk_score": payload.score,
            "triggered_rules": payload.triggered_rules,
            "reasons": payload.rule_reasons,
            "console_link": payload.console_link,
            "timestamp": payload.timestamp.isoformat()
        }

        try:
            client = self._get_client()
            response = client.publish(
                TopicArn=self.topic_arn,
                Subject=f"CRITICAL FRAUD ALERT - Risk Score {payload.score} (Account {payload.account_id})",
                Message=json.dumps(message),
                MessageAttributes={
                    "risk_score": {"DataType": "Number", "StringValue": str(payload.score)},
                    "account_id": {"DataType": "String", "StringValue": payload.account_id}
                }
            )
            logger.info(f"SNS alert successfully published to {self.topic_arn}, MessageId: {response.get('MessageId')}")
            return True
        except (BotoCoreError, ClientError) as ex:
            logger.error(f"Failed to publish to SNS ({self.topic_arn}): {ex}")
            return False
