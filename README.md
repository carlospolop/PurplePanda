# PurplePanda
![](https://github.com/carlospolop/PurplePanda/raw/master/images/logo.png)

This tool fetches resources from different cloud/saas applications focusing on permissions in order to **identify privilege escalation paths and dangerous permissions** in the cloud/saas configurations. Note that PurplePanda searches both **privileges escalation paths within a platform and across platforms**.

The name comes from the animal **Red Panda**. This panda eats peas, just like Purple Panda, which can ingest API keys/tokens found by these **[PEASS](https://github.com/carlospolop/PEASS-ng)**. The color was changed to purple because this tool is meant mainly for **Purple Teams** (because it can be **highly useful for both Blue and Red Teams**).

## How to use
Each folder inside `/intel` defines one platform that can be enumerated and **contains a README.md file explaining how to use that specific module**.

Download **[Neo4jDesktop](https://neo4j.com/download-center/#desktop)** and create a database. Then **export the env variables `PURPLEPANDA_NEO4J_URL` and `PURPLEPANDA_PWD`** with the URL to the neo4j database and the password.

If you want **shodan** to be used with public IPs discovered during the enumeration **export a env variable called *SHODAN_KEY* with a valid api key of shodan**.

Then just install and launch the program indicating the platforms you want to enumerate comma separated like.

### Local install
```bash
git clone https://github.com/carlospolop/PurplePanda
cd PurplePanda
python3 -m venv .
source bin/activate
python3 -m pip install -r requirements.txt
export PURPLEPANDA_NEO4J_URL="bolt://neo4j@localhost:7687"
export PURPLEPANDA_PWD="neo4j_pwd_4_purplepanda"
python3 main.py -h # Get help
python3 main.py -e -p google,github,k8s --github-only-org --k8s-get-secret-values --gcp-get-secret-values # Enumerate google, github and k8s
```

### Docker
```bash
# Consider adding the API keys in the Dockerfile
docker rm -f purplepanda
docker build --tag=purplepanda .
# Execute -h
## CHange -h for the params you want to run purplepanda with
docker run -t \
    -e PURPLEPANDA_NEO4J_URL="bolt://neo4j@host.docker.internal:7687" \
    -e PURPLEPANDA_PWD="s3cr3t" \
    -e GOOGLE_DISCOVERY=... \
    -e GITHUB_DISCOVERY=... \
    -e K8S_DISCOVERY=... \
    -e CONCOURSE_DISCOVERY=... \
    -e CIRCLECI_DISCOVERY=... \
    purplepanda python3 main.py -h

## -t is needed to see the output properly
## If you are using Neo4Desktop to connec to the DB use the domain host.docker.internal
## You might need to use the option '-v' to mount files with configurations
```

PurplePanda has **2 analysis modes**:
- `-e` (*enumerate*): This is the **main one**, it will try to gather data and analyze it.
- `-a` (*analyze*): This will perform a **quick analysis of the provided credentials**.

### Video tutorial
Check how to use and inspect the data gathered by PurplePanda:

[![Tutorial](https://img.youtube.com/vi/zl5NdvoWHX4/0.jpg)](https://www.youtube.com/watch?v=zl5NdvoWHX4)

### For Blue/Purple Teams

Use credentials for each platform with at least **admin read access to all the resources** of the platform. This will help you to see exactly the **privesc paths** that can be abused within your configurations in each platform and across

### For Red Teams

PurplePanda is also **designed to be used by Red Teams**. In general, cloud/saas platforms **won't give everyone access to read** the configuration of the platform, that's why PurplePanda supports the **use of several keys for the same platform**, in order to try to enumerate everything with all the keys you compromised and have the most accurate view of the configuration of the platform.

## Supported platforms
- **Google Cloud Platform (GCP)**: To understand how GCP security works and how to abuse roles and permissions **read https://cloud.hacktricks.xyz/pentesting-cloud/gcp-security**
- **Github**: To understand how Github security works and how to bypass branch protections, steal secrets, privesc... **read https://cloud.hacktricks.xyz/pentesting-ci-cd/github-security**
- **Kubernetes (K8s)**: To understand how Kubernetes RBAC security works and how to abuse roles, privesc to other clouds... **read https://cloud.hacktricks.xyz/pentesting-cloud/kubernetes-security**


## How to use the data
**Use the `-d` parameter** indicating a directory. Then, **PurplePanda will write in this directory several interesting analysis** in `csv` format of the information obtained from all the platforms. The recommendation is to **find interesting and unexpected things in those files** and then move to **analyze those interesting cases with the graphs**.

Each folder inside `/intel` defines one platform that can be enumerated and **contains a README.md file explaining how to use that specific module**. Moreover, each folder also contains a `HOW_TO_USE.md` file and a `QUERIES.md` file. 

In the `HOW_TO_USE.md` file you can find the **best queries to perform an investigation on how to escalate privileges** (*for Purple, Blue, and Red Teams*).

In the `QUERIES.md` file you will find **all proposed queries** to investigate the data easier.

### How to visualize the data in graphs
Follow the instructions indicated in **[VISUALIZE_GRAPHS.md](https://github.com/carlospolop/PurplePanda/blob/master/VISUALIZE_GRAPHS.md)**

## How to Contribute

In the **root folder and in each folder inside `intel/`** you will find a **`TODO.md` file**. You can find in those files how you can help. Just **send a PR with the addition**.

**PRs with fixes** are also welcome :)

Moreover, if you have **other ideas** that aren't in those TODO files feel free to send a PR.


By Carlos Polop<sup>TM</sup>
