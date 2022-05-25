# Github Discovery Module
This module allows you to discover the following **Github resources**:
- Organizations
- Users
- Teams
- Repos
- Branches
- Secrets
- Leaks
- Self hosted runners
- Privileges

To **understand how Github security works** and how to bypass branch protections, steal secrets, privesc... **read https://book.hacktricks.xyz/cloud-security/github-security**


## How to start
After installing PurplePanda you need to **export the `GITHUB_DISCOVERY` env** variable with a yaml encoded in **base64** with the information of the account to use.
There are the attribute the config env var supports:
```yaml
github:
- token: "string"
  username: "string"
  password: "string"
  url: "https://api.github.com/graphql"
  org_name: "string"

# At least token or username+password need to be configured
# URL is optional, provide it ONLY if needed
# org_name can be empty or unexistent (but better if provided to use more specific options)
```

The **only mandatory param is `token` or `username` and `password`**. 

Another **important attribute is `org_name`**, usually you will use PurplePanda to check the privileges of an organization, in that scenario it's recommended to configure the org name in this parameter.

If you are creating a token specifically for PurplePanda give it the permissions: `repo` (`repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `repository`), `read:org`, and `read:enterprise`.
 security_events

Example:
```yaml
github:
- token: "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
  org_name: "org_name"
```
Just encode in base64 that file and export it in the `GITHUB_DISCOVERY` env var and you will be ready to **use the github module**:
```bash
export GITHUB_DISCOVERY="Z2l0aHViOgotIHRva2VuOiAiQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBQUFBIgogIG9yZ19uYW1lOiAib3JnX25hbWUiCg=="
python3 main.py -p github --github-only-org -e
```

### Github module params
- `--github-only-org-and-org-users`: By default github module is going to get all the info it can, it's recommended to use this attribute to focus just in the indicated organization in the config env variable. This will get all the info of the org and also all the info of each member.
- `--github-only-org`: By default github module is going to get all the info it can, it's recommended to use this attribute to focus just in the indicated organization in the config env variable. This will only get all the info of the org. PARAM RECOMMENDED TO AUDIT JUST ONE ORGANIZATION. 
- `--github-all-branches`: By default github module just get the default branch of each repo, indicate this attr to get all (not recommended).
- `--github-no-leaks`: By default github module runs [gitleaks](https://github.com/zricethezav/gitleaks) on each repo, use this flag to not do that (might run faster).
- `--github-get-redundant-info`: By default github module try to avoid to get the same info 2 times, use this flag if you think you can find more info.
- `--github-get-archived`: By default archived repos aren't analyzed (just basic info is gathered), use this flag to treat them as non-archived repos

## Permissions configuration
If you are part of a **Blue Team or Purple Team**, I would suggest you to launch this module with an **account with at least `get` and `list` permissions over all the resources** this module is searching.

If you are part of a **Red Team**, just launch it with **all the credentials** you managed to obtain.

## How to use the data
**Use the `-d` parameter** indicating a directory. Then, **PurplePanda will write in this directory several interesting analysis** in `csv` format of the information obtained from all the platforms. The recommendation is to **find interesting and unexpected things in those files** and then move to **analyze those interesting cases with the graphs**.

In the [`HOW_TO_USE.md`](./HOW_TO_USE.md) file you can find the **best queries to perform an investigation on how to escalate privileges** (*for Purple, Blue, and Red Teams*).

In the [`QUERIES.md`](./QUERIES.md) file you will find **all proposed queries** to investigate the data easier.

### How to visualize the data in graphs
Follow the instructions indicated in **[VISUALIZE_GRAPHS.md](https://github.com/carlospolop/PurplePanda/blob/master/VISUALIZE_GRAPHS.md)**
