"""
src.notification_service
~~~~~~~~~~~~~~~~~~~~~~~~

Sample domain service demonstrating automated architecture documentation generation.
"""

from typing import List, Optional, Dict


class NotificationService:
    """
    Coordinates multi-channel delivery of transactional alerts, emails, and SMS notices.
    """

    def __init__(self, email_gateway: str, sms_gateway: str, max_retries: int = 3):
        """
        Initializes the notification service with required third-party dispatch providers.
        """
        self.email_gateway = email_gateway
        self.sms_gateway = sms_gateway
        self.max_retries = max_retries
        self.dispatch_history: List[Dict[str, str]] = []

    def send_email(self, recipient: str, subject: str, message_body: str) -> bool:
        """
        Transmits an email alert via the configured email delivery gateway.
        """
        if not recipient or not message_body:
            return False
        
        record = {"channel": "email", "to": recipient, "status": "sent"}
        self.dispatch_history.append(record)
        return True

    def send_sms(self, phone_number: str, text: str) -> bool:
        """
        Dispatches a short message service alert to the destination mobile subscriber.
        """
        if not phone_number or len(phone_number) < 10:
            return False
            
        record = {"channel": "sms", "to": phone_number, "status": "queued"}
        self.dispatch_history.append(record)
        return True

    def get_dispatch_summary(self) -> Dict[str, int]:
        """
        Aggregates delivery statistics grouped by communication channel.
        """
        summary = {"email": 0, "sms": 0}
        for item in self.dispatch_history:
            channel = item.get("channel", "unknown")
            if channel in summary:
                summary[channel] += 1
        return summary
