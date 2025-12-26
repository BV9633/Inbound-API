from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID, TABLE_ID

client = bigquery.Client(project=PROJECT_ID)

def get_invoice_data(invoice_id: str):
    query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        WHERE invoice_id = @invoice_id
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter(
                "invoice_id", "STRING", invoice_id
            )
        ]
    )

    rows = client.query(query, job_config=job_config).result()
    return [dict(row) for row in rows]