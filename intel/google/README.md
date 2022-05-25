# Google Discovery Module
This module allows you to discover the following **GCP and Workspace resources**:
- Workspace companies
- Workspace users and groups
- Bigquery
- Cloud Functions
- Cloud Run
- Cloud Build
- GKE
- Composer
- Compute and networks
- Folders
- Organizations
- Permissions and roles
- Projects
- Pub/Sub
- Secrets
- Service Accounts
- Source Repos
- Storage
- KMS

To **understand how GCP security works** and how to abuse roles and permissions **read https://book.hacktricks.xyz/cloud-security/gcp-security**


## How to start
After installing PurplePanda you need to **export the `GOOGLE_DISCOVERY` env** variable with a yaml encoded in **base64** with the information of the account to use.
There are the attribute the config env var supports:
```yaml
google:
- file_path: "string"
  quota_project_id: "string"
  service_account_id: "string"
  scopes:
    - "https://www.googleapis.com/auth/cloud-platform"

# file_path is the path to the JSON file containing the user/service account credentials. It's mandatory, if empty default file is used.
# quota_project_id is optional, provide the name of the project.
# service_account_id is optional, provide the same of the service account to impersonate to enumerate the environment.
# scopes is optional, provide a list of scopes if you whish.
```

The **only mandatory param is `file_path`**, which should indicate the **path to the JSON containing the credentials** of the principal. If nothing is specified the default app credenctials file is used (generally created with `gcloud auth application-default login` and located in `$HOME/.config/gcloud/application_default_credentials.json`)

Another **important attribute is `service_account_id`**, where you can indicate the **SA you want to impersonate** (if any).

Example:
```yaml
google:
- file_path: ""

- file_path: ""
  service_account_id: "some-sa-email@sidentifier.iam.gserviceaccount.com"
```
Just encode in base64 that file and export it in the `GOOGLE_DISCOVERY` env var and you will be ready to **use the google module**:
```bash
gcloud auth login
gcloud auth application-default login
export GOOGLE_DISCOVERY="Z29vZ2xlOgotIGZpbGVfcGF0aDogIiIKCi0gZmlsZV9wYXRoOiAiIgogIHNlcnZpY2VfYWNjb3VudF9pZDogInNvbWUtc2EtZW1haWxAc2lkZW50aWZpZXIuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iCg=="
python3 main.py -p google --gcp-get-secret-values -e
```

### Google module params
- `--gcp-get-secret-values`: Use this param to indicate to PurplePanda to try to get the secret values (*by default no secrets values ara gathered*)

## Permissions configuration
If you are part of a **Blue Team or Purple Team**, I would suggest you to launch this module with an **account with at least the following roles over the organization**:
- roles/bigquery.metadataViewer
- roles/composer.user
- roles/compute.viewer
- roles/container.clusterViewer
- roles/iam.securityReviewer
- roles/resourcemanager.folderViewer
- roles/resourcemanager.organizationViewer
- roles/secretmanager.viewer

If you are part of a **Red Team**, just launch it with **all the credentials** you managed to obtain.

## Important to note
**GCP has thousands of permissions**. This tool **knows about some of them** that are interesting and can be abused to escalate privleges, but it might be possible to abuse others **unknown** by this tool. Therefore, if you know about **other permissions that could be abused to escalate privileges, please, send a PR or create a github issue** indicating so.

**GCP has more resource** than the ones gathered by this tool. This means that this tool might not found some possible privileges escalations. If you are interested in this tool getting some specifig resources feel free to develop that part and **send a PR, or create a github issue** indicating the resources you would like this tool to get and how could they be used to escalate privileges.


## How to use the data
**Use the `-d` parameter** indicating a directory. Then, **PurplePanda will write in this directory several interesting analysis** in `csv` format of the information obtained from all the platforms. The recommendation is to **find interesting and unexpected things in those files** and then move to **analyze those interesting cases with the graphs**.

In the [`HOW_TO_USE.md`](./HOW_TO_USE.md) file you can find the **best queries to perform an investigation on how to escalate privileges** (*for Purple, Blue, and Red Teams*).

In the [`QUERIES.md`](./QUERIES.md) file you will find **all proposed queries** to investigate the data easier.

### How to visualize the data in graphs
Follow the instructions indicated in **[VISUALIZE_GRAPHS.md](https://github.com/carlospolop/PurplePanda/blob/master/VISUALIZE_GRAPHS.md)**
