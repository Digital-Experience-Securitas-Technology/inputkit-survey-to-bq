# inputkit-survey-to-bq
This Repo is for Storing code base for cloud function in GCP

Step 1 - Create a folder on your local machine or Cloud Shell
<!-- mkdir inputkit-webhook -->
<!-- cd inputkit-webhook -->

Step 2 - Create main.py
<!-- Change the table name and entry point function name -->

Step 3 - Enable Required Google Cloud APIs if not
<!-- gcloud services enable \
    cloudfunctions.googleapis.com \
    run.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    bigquery.googleapis.com -->

Step 4 - Create BigQuery Dataset (correct region!) if not
<!-- bq --location=asia-south1 mk Raw_Inputkit_Surv -->

Step 5 - Grant Service Account Permissions if not
<!-- gcloud projects add-iam-policy-binding advanced-analytics-397015 \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.dataEditor"

gcloud projects add-iam-policy-binding advanced-analytics-397015 \
  --member="serviceAccount:PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/bigquery.jobUser" -->

Step 6 - Deploy the Cloud Function (v2)
<!-- cd ~/inputkit-webhook-service -->

<!-- gcloud functions deploy inputkit-webhook-service \
  --gen2 \
  --region=asia-south1 \
  --runtime=python310 \
  --source=. \
  --entry-point=inputkit_webhook \
  --trigger-http \
  --allow-unauthenticated \
  --service-account=892632373166-compute@developer.gserviceaccount.com -->

Step 7 - Get Your Function URL
<!-- example : https://us-central1-advanced-analytics-397015.cloudfunctions.net/inputkit-webhook -->

Step 8 - Test Using cURL
<!-- curl -X POST \
  "https://us-central1-advanced-analytics-397015.cloudfunctions.net/inputkit-webhook?token=Xx93jksdf8DFjklsf9032" \
  -H "Content-Type: application/json" \
  -d '{"hello":"world"}' -->


