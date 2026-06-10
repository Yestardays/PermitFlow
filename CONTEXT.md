# PermitFlow Domain Context

PermitFlow is a Chinese-language Feishu bot for self-service permission applications.
It identifies one permission item, gathers only missing fields, shows an editable confirmation
card, and creates a Jira issue after explicit confirmation.

## Terms

- **Permission item**: maintained knowledge describing one requestable access grant.
- **Application**: a user's in-progress, self-only request.
- **Candidate**: a possible permission item returned by fuzzy retrieval.
- **Confirmation card**: the final editable Feishu card before Jira submission.
- **Fallback draft**: escaped prefilled text and a service desk URL returned after Jira failure.

## Hard boundaries

- No approval, provisioning, or claims that access has been granted.
- No proxy applications in Phase 1; applicant identity comes from Feishu.
- Every application has a fixed validity period; sensitive items cannot be permanent.
- A Jira ticket link ends the workflow. Tracking and reminders are optional Phase 3 notifications.

