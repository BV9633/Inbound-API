import os
from dotenv import load_dotenv
load_dotenv()
from google.cloud import bigquery,parametermanager_v1


project_id= os.getenv('DDT_PROJECT_ID')
dataset_id = os.getenv('DDT_DATASET_ID')
table_id = os.getenv('DDT_TABLE_ROLE_ID')
 
 
from google.auth import default
 
def get_impersonated_credentials(target_sa_email, scopes):
    """Impersonate a service account using the Cloud Run SA"""
    from google.auth import impersonated_credentials
   
    # Get default credentials (Cloud Run SA)
    source_credentials, _ = default()
   
    # Create impersonated credentials
    target_credentials = impersonated_credentials.Credentials(
        source_credentials=source_credentials,
        target_principal=target_sa_email,
        target_scopes=scopes,
    )
   
    return target_credentials
 
# Use in your clients
def get_bigquery_client():
    try:
        bigquery_creds = get_impersonated_credentials(
            'sa-ddt-bigquery@its-compute-sc-darkdata-p.iam.gserviceaccount.com',
            ['https://www.googleapis.com/auth/bigquery']
        )
        client = bigquery.Client(credentials=bigquery_creds, project="its-compute-sc-darkdata-p")
        return client
    except Exception as e:
        print(e)
        print("*"*60)

def get_secretmanager_client():
    try:
        secretmanager_creds = get_impersonated_credentials(
            'sa-ddt-security@its-compute-sc-darkdata-p.iam.gserviceaccount.com',
            ['https://www.googleapis.com/auth/cloud-platform']
        )
        client = secretmanager.SecretManagerServiceClient(credentials=secretmanager_creds)
        return client
    except Exception as e:
        print(e)
        print("*"*60)

def get_parametermanager_client():
    try:
        parametermanager_creds = get_impersonated_credentials(
            'sa-ddt-security@its-compute-sc-darkdata-p.iam.gserviceaccount.com',
            ['https://www.googleapis.com/auth/cloud-platform']
        )
        client = parametermanager_v1.ParameterManagerClient(credentials=parametermanager_creds)
        return client
    except Exception as e:
        print(e)
        print("*"*60)

def get_parameter_labels(
    project_id: str,
    location: str,
    parameter_id: str,
    ):
    client = get_parametermanager_client()
 
    parameter_name = f"projects/{project_id}/locations/{location}/parameters/{parameter_id}"
 
    # Fetch parameter metadata
    parameter = client.get_parameter(name=parameter_name)
 
    # Labels are a dictionary
    labels = parameter.labels
 
    return dict(labels)
       
