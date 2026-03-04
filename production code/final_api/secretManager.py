from google.cloud import secretmanager
import logging
from Service_imperson import get_secretmanager_client
# Setup Logging
logger = logging.getLogger(__name__)

def access_secret_variable(project_id, secret_names, version_id='latest'):

    """
    Accesses a secret version and returns its payload.
    """

    try:
        # Create the Secret Manager client.
        # client = secretmanager.SecretManagerServiceClient()
        client = get_secretmanager_client()
        secrets = {}
        for secret_name in secret_names:
            # Build the resource name of the secret version.
            name = f"projects/{project_id}/secrets/{secret_name}/versions/{version_id}"
            # Access the secret version.
            response = client.access_secret_version(request={"name": name})
            # Extract the payload (secret value) as a string.
            secrets[secret_name] = response.payload.data.decode("UTF-8")
        return secrets

    except Exception as e:
        logger.critical("Error accessing secret: %s", e)
        return None