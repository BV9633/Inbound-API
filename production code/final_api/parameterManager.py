from google.cloud import parametermanager_v1
from Service_imperson import get_parametermanager_client
 
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
 
 
# Example usage
# try:
#  labels = get_parameter_labels(
#      project_id="its-compute-sc-rmapchat-d",
#      location="global",
#      parameter_id="DARK_DATA_TRANSFORMATION"
#  )
  
#  print("Labels:", type(labels))
  
#  # Access specific label
#  print("ext processor id:", labels.get("extractor_processor_id"))
#  print("bucket_name:", labels.get("bucket_name"))
# except Exception as e:
#  print("exception:", e)