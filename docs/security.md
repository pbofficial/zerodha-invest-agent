# Enterprise Security Guide

## 1. Secrets Management
- **Never Hardcode Secrets**: All API keys (Zerodha, OpenAI, Apigee) are stored in **Google Secret Manager**.
- **Access Control**: Only the `zerodha-agent-sa` Service Account has `secretAccessor` permissions.
- **Rotation**: Rotate `KITE_ACCESS_TOKEN` daily. Rotate API keys quarterly.

## 2. Network Security (VPC-SC)
For Enterprise deployments, we recommend **VPC Service Controls**:
1. Create a **Service Perimeter** encompassing Cloud Functions, Secret Manager, and Apigee.
2. Restrict Ingress/Egress to allow ONLY the Agent's specific traffic.
3. This prevents data exfiltration even if credentials are compromised.

## 3. Identity & Access Management (IAM)
- **Principle of Least Privilege**: The `zerodha-agent-sa` has granular roles (e.g., `roles/datastore.user`, `roles/run.invoker`).
- **Invoker Restrictions**: 
    - Cloud Functions should **NOT** have `allUsers` allowed.
    - Only the Service Account associated with the Apigee proxy should have `run.invoker` permission.

## 4. Terraform State
- **Current**: Local state (`terraform.tfstate`).
- **Recommended**: Move state to a **Remote Backend** (GCS Bucket) with Object Versioning and strict IAM permissions to prevent state corruption or leakage of output variables.

## 5. Logging Audit
- **Sanitization**: The codebase is audited to ensure `print()` statements do not output sensitive payloads (like full portfolio JSONs with account IDs).
- **Retention**: Configure Cloud Logging retention policies (e.g., 30 days) to comply with compliance standards.
