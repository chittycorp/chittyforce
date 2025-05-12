# 🔐 SecureKey: Autonomous Workspace Control Agent

## 🧠 Overview
SecureKey is a production-grade FastAPI microservice designed to give GPT agents and backend automations **full control over Google Workspace** via secure APIs. It enables programmatic access to **Google Drive, Docs, Sheets, and Slides**, scoped to both individual and shared drives, with smart behaviors like folder path resolution, aliasing, and document manipulation.

This agent is **stateless**, deployable to **Google Cloud Run**, and protected by a **bearer API key**.

## 🚀 Key Features
- Full control over Drive, Docs, Sheets, and Slides
- Autonomous path resolution and folder tree creation
- Smart document text handling (append, replace, clear)
- Cloud Run-compatible, Dockerized deployment
- Modular, extensible FastAPI code structure

## 🔧 Deployment

```bash
gcloud builds submit --tag gcr.io/genie-patch-v1-0/securekey

gcloud run deploy securekey \
  --image gcr.io/genie-patch-v1-0/securekey \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_SA_KEY_FILE=genie-patch-v1-0-ad49d3dc43a7.json,API_KEY=your_actual_api_key_here
```

## 🔍 Debug Locally

```bash
docker build -t securekey-test .
docker run -e API_KEY=devtest -e GOOGLE_SA_KEY_FILE=creds.json -p 8080:8080 securekey-test
```
