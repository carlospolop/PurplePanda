## Resources to list and get permissions from
- Big query (row rules)
- Firestore databases
- Check if a service account has access over other users workspaces (https://book.hacktricks.xyz/cloud-security/gcp-security#spreading-to-g-suite-via-domain-wide-delegation-of-authority) - This technique requires to impersonate each SA to check if it can impersonate each user (not feasible)
- CloudSQL
- Cloud Tasks
- Use Bucket ACLs
- Based on https://stackoverflow.com/questions/39860726/google-api-client-container-registry-api-python get images inside registry usng a docker API library
    - Check if public access is possible
    - If not, you need to send the auth token (gcloud container images list --repository=eu.gcr.io/name_repo --log-htt)
    - Relate this with cloudbuild builds
    - Use googleapiclient.discovery.build("containeranalysis", "v1", credentials=cred, cache_discovery=False) to get notes and vulnerabilities of the images
- Check if current user can impersonate each discovered SA
    -   Offer to automatically impersonate the ones that he can and rerun the analysis
- Apply x-goog-user-project header when the API service isn't enabled i the billing project
- Anyway that can write in the composer dags bucket, can escalate to the running cluster SA

## Privilege Escalation paths
- Find SAs without .name as those are SAs not managed by the organization


## Privesc through kubernetes
- If not private and any container permission of K8s, escalate to the RUN_IN SA or to all the RUN_IN SAs in clusters that are public
- If possible, download kubectl creds file and run K8s discovery


