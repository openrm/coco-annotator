from urllib.parse import urlparse

cs_client = None

def sign_url(uri, expiration=None, content_type=None):
    parsed = urlparse(uri)
    if parsed.scheme == 'gs':
        from google.cloud.storage import Client, Blob

        global cs_client
        if cs_client is None:
            cs_client = Client()

        blob = Blob.from_string(uri, client=cs_client)
        return blob.generate_signed_url(
            expiration=expiration,
            content_type=content_type)
    else:
        raise NotImplementedError
