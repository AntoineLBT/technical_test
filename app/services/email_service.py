import logging
from email.mime.text import MIMEText

from aiosmtplib import SMTPException, send

from app.config import settings

logger = logging.getLogger(__name__)

_FROM_ADDRESS = "noreply@dailymotion.com"


class EmailService:
    def __init__(
        self,
        smtp_host: str = settings.mailhog_smtp_host,
        smtp_port: int = settings.mailhog_smtp_port,
    ) -> None:
        self._smtp_host = smtp_host
        self._smtp_port = smtp_port

    async def send_activation_code(self, to_email: str, code: str) -> None:
        message = MIMEText(
            f"Your Dailymotion activation code is: {code}\n"
            "This code expires in 1 minute."
        )
        message["From"] = _FROM_ADDRESS
        message["To"] = to_email
        message["Subject"] = "Your Dailymotion activation code"

        try:
            await send(
                message,
                hostname=self._smtp_host,
                port=self._smtp_port,
            )
            logger.info("Activation code sent to %s", to_email)
        except SMTPException as exc:
            logger.error("Failed to send activation email to %s: %s", to_email, exc)
            raise
