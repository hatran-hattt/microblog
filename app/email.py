import asyncio
from flask import render_template
from flask_mail import Message
from app import app, mail


def _send_email(app_instance, msg):
    with app_instance.app_context():
        mail.send(msg)


async def send_password_reset_email_asyncio(user):
    username = user.get_display_name()
    token = user.get_reset_password_token()
    body = render_template(
        "email/reset_password.txt",
        username=username,
        token=token,
    )
    html = render_template(
        "email/reset_password.html",
        username=username,
        token=token,
    )

    msg = Message(
        "[Microblog] Reset password",
        [user.email],
        body,
        html,
        sender=app.config["MAIL_ADMINS"][0],
    )

    # Schedule the blocking call to run in a separate thread managed by asyncio
    # current_app._get_current_object() ensures we pass the actual app instance
    await asyncio.to_thread(lambda: _send_email(app, msg))
