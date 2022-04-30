# Concourse Discovery Module
This module allows you to discover the following **Concourse resources**:
- Users
- Groups
- Teams
- Pipelines
- PipelineGroups
- Jobs
- Resources
- Workers
- Secrets

To **understand how Concourse works** and how to abuse roles, leak secrets, privesc to other clouds... **read https://book.hacktricks.xyz/cloud-security/pentesting-concourse**


## How to start
After installing PurplePanda you need to **export the `CONCOURSE_DISCOVERY` env** variable with a yaml encoded in **base64** with the information of the account to use.
There are the attribute the config env var supports:
```yaml
concourse:
- token: "string"
  url: "string"

- username: "string"
  password: "string"
  url: "string"

# (token || (username + password)) + url is mandatory
```

The **only mandatory params are `url` and `token` or `username and password`**. 

Example:
```yaml
concourse:
  - uri: http://127.0.0.1:8080
    token: 9rEpFtDcE1234aIuwVNEn+jok24E9jNiAAAAAA
```
Just encode in base64 that file and export it in the `CONCOURSE_DISCOVERY` env var and you will be ready to **use the concourse module**:
```bash
export CONCOURSE_DISCOVERY="Y29uY291cnNlOgogIC0gdXJpOiBodHRwOi8vMTI3LjAuMC4xOjgwODAKICAgIHRva2VuOiA5ckVwRnREY0UxMjM0YUl1d1ZORW4ram9rMjRFOWpOaUFBQUFBQQo="
python3 main.py -p concourse -e
```

## Permissions configuration
The most basic concourse role should be enough to **enumerate** almost everything.

## Important to note
Feel free to submit **PRs enumerating other concourse resources/protections and taking them into account** when trying to discover privilege escalation paths.

## How to use the data
**Use the `-d` parameter** indicating a directory. Then, **PurplePanda will write in this directory several interesting analysis** in `csv` format of the information obtained from all the platforms. The recommendation is to **find interesting and unexpected things in those files** and then move to **analyze those interesting cases with the graphs**.

In the [`HOW_TO_USE.md`](./HOW_TO_USE.md) file you can find the **best queries to perform an investigation on how to escalate privileges** (*for Purple, Blue, and Red Teams*).

In the [`QUERIES.md`](./QUERIES.md) file you will find **all proposed queries** to investigate the data easier.

### How to visualize the data in graphs
Follow the instructions indicated in **[VISUALIZE_GRAPHS.md](https://github.com/carlospolop/PurplePanda/blob/master/VISUALIZE_GRAPHS.md)**
