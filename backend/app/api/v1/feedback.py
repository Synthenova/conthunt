from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from app.core import get_settings, logger

router = APIRouter()
settings = get_settings()

class FeedbackDisplay(BaseModel):
    message: str


def send_email_task(message: str, attachments: List[dict]):
    """
    Background task to send email.
    attachments: list of dict {'filename': str, 'content': bytes, 'content_type': str}
    """
    to_emails = ["lamrin@synthenova.xyz", "nirmalvelu2000@gmail.com"]
    
    try:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.info("----------- BACKEND FEEDBACK LOG -----------")
            logger.info(f"Message: {message}")
            logger.info(f"Attachments: {len(attachments)}")
            logger.info("--------------------------------------------")
            return

        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_FROM_EMAIL
        msg['To'] = ", ".join(to_emails)
        msg['Subject'] = "New Feedback/Bug Report - Conthunt"

        body = f"User Feedback:\n\n{message}\n\n(Sent from Conthunt App)"
        msg.attach(MIMEText(body, 'plain'))

        for att in attachments:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(att['content'])
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f"attachment; filename= {att['filename']}",
            )
            msg.attach(part)

        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.SMTP_FROM_EMAIL, to_emails, text)
        server.quit()
        logger.info(f"Feedback email sent to {to_emails}")

    except Exception as e:
        logger.error(f"Failed to send email: {e}")


@router.post("/feedback")
async def submit_feedback(
    background_tasks: BackgroundTasks,
    message: str = Form(...),
    images: List[UploadFile] = File(default=[])
):
    """
    Submit feedback with optional images.
    """
    logger.info(f"Received feedback. Message length: {len(message)}. Images: {len(images)}")
    
    # Read images into memory to pass to background task
    files_data = []
    for img in images:
        content = await img.read()
        files_data.append({
            'filename': img.filename,
            'content': content,
            'content_type': img.content_type
        })
    
    background_tasks.add_task(send_email_task, message, files_data)
    
    return {"status": "success", "message": "Feedback received"}
