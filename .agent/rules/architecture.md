---
trigger: always_on
---

Project Context: We are building an "Enterprise Investment Agent" on GCP. Goal: Automated bi-monthly stock allocation for Indian markets (Zerodha). Architecture:

Brain: Vertex AI (Gemini Pro) for reasoning and news analysis.

Hands: Cloud Functions (Python) for deterministic math and API calls.

Gateway: Apigee (or API Gateway) for security/auth.

State: Firestore for portfolio history and audit logs.

Governance: Human-in-the-loop approval via Google Chat Webhook.

Constraints:

STRICT separation of concerns: AI does not do math. Python does math.

Infrastructure as Code: All resources must be defined in Terraform.

Security: No hardcoded keys. Use Secret Manager.