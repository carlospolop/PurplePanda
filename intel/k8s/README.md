# K8s Discovery Module
This module allows you to discover the following **Kubernetes resources**:
- Namespaces
- Nodes
- Pods
- Containers
- Volumes
- Secrets
- Environment Variables
- Service Accounts
- Users
- Groups
- Roles/ClusterRoles,RoleBindings/ClusterRoleBindings
- Services
- Ingresses

To **understand how Kubernetes RBAC security works** and how to abuse roles, privesc to other clouds... **read https://book.hacktricks.xyz/cloud-security/pentesting-kubernetes**


## How to start
After installing PurplePanda you need to **export the `K8S_DISCOVERY` env** variable with a yaml encoded in **base64** with the information of the account to use.
There are the attribute the config env var supports:
```yaml
k8s:
- token: "string"
  url: "string"
  cluster_id: "Home_Clusters"

- file_path: "string"
  cluster_id: "GCP-GKE-Name"

# token + url or file_path is mandatory
```

The **only mandatory param is `token` and `url`** or **`file_path`** indicating the path to the kubeconfig file. 

For Purple and Blue Teams, you should give at least **get/list/watch permission over all the listed resources across all the cluster** to the credentials you are going to use to enumerate the cluster.

Example:
```yaml
k8s:
  - file_path: /path/to/kubeconf.txt
```
Just encode in base64 that file and export it in the `K8S_DISCOVERY` env var and you will be ready to **use the github module**:
```bash
export K8S_DISCOVERY="azhzOgogIC0gZmlsZV9wYXRoOiAvcGF0aC90by9rdWJlY29uZi50eHQK"
python3 main.py -p k8s --k8s-get-secret-values -e
```

### K8s module params
- `--k8s-get-secret-values`: By default k8s secrets are not retreived, use this flag to retreive them.

## Permissions configuration
If you are part of a **Blue Team or Purple Team**, I would suggest you to launch this module with an **account with at least `get` and `list` permissions over all the resources** this module is searching.

If you are part of a **Red Team**, just launch it with **all the credentials** you managed to obtain.

## Important to note
PurplePanda performs an **analysis of the RBAC data collected** from the kubernetes cluster and tries to **find privilege escalation paths according to the discovered data**. However, in kubernetes it's possible to **force protections in more ways** (like PodSecurityPolicies and more), so it's possible that when trying to follow a discovered path you find that it's not possible to exploit it.

Feel free to submit **PRs enumerating other kubernetes protections and taking them into account** when trying to discover privilege escalation paths.

## How to use the data
**Use the `-d` parameter** indicating a directory. Then, **PurplePanda will write in this directory several interesting analysis** in `csv` format of the information obtained from all the platforms. The recommendation is to **find interesting and unexpected things in those files** and then move to **analyze those interesting cases with the graphs**.

In the [`HOW_TO_USE.md`](./HOW_TO_USE.md) file you can find the **best queries to perform an investigation on how to escalate privileges** (*for Purple, Blue, and Red Teams*).

In the [`QUERIES.md`](./QUERIES.md) file you will find **all proposed queries** to investigate the data easier.

### How to visualize the data in graphs
Follow the instructions indicated in **[VISUALIZE_GRAPHS.md](https://github.com/carlospolop/PurplePanda/blob/master/VISUALIZE_GRAPHS.md)**
