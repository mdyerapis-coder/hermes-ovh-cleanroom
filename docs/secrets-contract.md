# Secrets contract

Authoritative names: `config/secret-contract.yaml`.

Rules:

- Never commit secret values
- HSP fails closed on missing required secrets
- Logs and evidence must redact values
- Bootstrap credentials only outside HSP when unavoidable
