from app import mail


def _send_email(app_instance, msg):
    with app_instance.app_context():
        mail.send(msg)
