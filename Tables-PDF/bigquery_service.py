from google.cloud import bigquery
from config import PROJECT_ID, DATASET_ID, TABLE_ID

def get_invoice_data(invoice_id: str):
    try:
        print(f"[BigQuery] Running query for invoice_id: {invoice_id}")

        client = bigquery.Client(project=PROJECT_ID)

        query = f"""
        SELECT *
        FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        WHERE invoice_id = @invoice_id 
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("invoice_id", "STRING", invoice_id)
            ]
        )

        results = client.query(query, job_config=job_config)
        rows = [dict(row) for row in results]

        print(f"[BigQuery] Rows fetched: {len(rows)}")
        return rows

    except Exception as e:
        print("[BigQuery ERROR]", str(e))
        raise