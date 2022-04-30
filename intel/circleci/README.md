# CirceCI Discovery Module
This module allows you to discover the following **CircleCI resources**:
- Orgs
- Contexts
- Projects
- Project Secrets
- Pipelines (there aren't pipelines objects in the DB because then there would be too many)

To **understand how CircleCI works** and how to abuse roles, leak secrets, privesc to other clouds... **read https://book.hacktricks.xyz/cloud-security/circleci**


## How to start
After installing PurplePanda you need to **export the `CIRCLECI_DISCOVERY` env** variable with a yaml encoded in **base64** with the information of the account to use.
There are the attribute the config env var supports:
```yaml
circleci:
- url: "string"
  token: "https://ci.example.com"
  org_slug: "github/org_name"
  projects: ["repo1", "repo2"]

# token is manadory, url, org_slug and projects are optional
```

The **only mandatory param is `token`** the others are optional.

Please, note that the **CircleCI API doesn't allow to numerate all the projects**. So this is the method followed to find as much as possible:
- Get the **projects followed** (if the user of the token is following all of them, then, all are found).
- Try to find the same **CircleCI org name as a github or bitbucket org** and then **seach each repo of that org** as CircleCI project.
- The user can indicate the project names in the **CIRCLECI_DISCOVERY environment variable in base64**.

If **CircleCI is launched while enumerating github**, circleci will be enumerated **after** a first round of enumeration (where **github** is enumerated) to not lose potential result.

Example:
```yaml
circleci:
  - token: 2047681a0c123e4f3cfea12301933768771db123
```
Just encode in base64 that file and export it in the `CIRCLECI_DISCOVERY` env var and you will be ready to **use the circleci module**:
```bash
export CIRCLECI_DISCOVERY="Y2lyY2xlY2k6CiAgLSB0b2tlbjogMjA0NzY4MWEwYzEyM2U0ZjNjZmVhMTIzMDE5MzM3Njg3NzFkYjEyMwo="
python3 main.py -p circleci -e
```

## Permissions configuration
A github owner (or bitbucket equivalent) is recommended to **enumerate** everything.

## Important to note
Feel free to submit **PRs enumerating other circleci resources/protections and taking them into account** when trying to discover privilege escalation paths.

## How to use the data
**Use the `-d` parameter** indicating a directory. Then, **PurplePanda will write in this directory several interesting analysis** in `csv` format of the information obtained from all the platforms. The recommendation is to **find interesting and unexpected things in those files** and then move to **analyze those interesting cases with the graphs**.

In the [`HOW_TO_USE.md`](./HOW_TO_USE.md) file you can find the **best queries to perform an investigation on how to escalate privileges** (*for Purple, Blue, and Red Teams*).

In the [`QUERIES.md`](./QUERIES.md) file you will find **all proposed queries** to investigate the data easier.

### How to visualize the data in graphs
Follow the instructions indicated in **[VISUALIZE_GRAPHS.md](https://github.com/carlospolop/PurplePanda/blob/master/VISUALIZE_GRAPHS.md)**
