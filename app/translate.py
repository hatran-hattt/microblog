from google.cloud import translate
from flask import current_app


def translate_text(text, source_language_code, target_language_code):

    client = translate.TranslationServiceClient()
    location = "global"
    parent = f"projects/{current_app.config["GOOGLE_CLOUD_TRANS_PROJECT_ID"]}/locations/{location}"

    response = client.translate_text(
        request={
            "parent": parent,
            "contents": [text],
            "mime_type": "text/plain",
            "source_language_code": source_language_code,
            "target_language_code": target_language_code,
        }
    )

    return response.translations.pop().translated_text
