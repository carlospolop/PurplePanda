# Investigation

In this section we are going to explain how to use PurplePanda to **find potential problems within your CircleCI environmentr** and possible **privilege escalation paths from CircleCI to other clouds**.

## Red, Purple & Blue Teams

Searching for **sensitive information in secrets and declared params** is something all the teams should do.
Moreover, checking who has **access as member, owner or admin** is also very important.

### Secrets

*You need to have enough permissions to retreive the secrets.*

<details>
<summary><b>Show queries to search secrets as, if stolen, it's higly probable that they contain sensitive information</b></summary>

#### Circleci - secrets
`Show all the secrets.`
  <details>
  <summary>e.g.: <i>Circleci - secrets</i></summary>
    <pre>
    MATCH(secret:CircleCISecret)
    RETURN secret</pre>
  </details>

#### Circleci - vars
`Show all the vars.`
  <details>
  <summary>e.g.: <i>Circleci - vars</i></summary>
    <pre>
    MATCH(var:CircleCIVar)
    RETURN var</pre>
  </details>

#### Circleci - secrets with projects
`Show all the secrets with their related pipelines.`
  <details>
  <summary>e.g.: <i>Councourse - secrets with pipelines</i></summary>
    <pre>
    MATCH(secret:CircleCISecret)<-[r:HAS_SECRET]-(project:CircleCIProject)
    RETURN secret,r,project</pre>
  </details>
</details>

### Vars

<details>
<summary><b>Show projects with vars defined as they might contain sensitive information</b></summary>

#### Circleci - vars with projects
`Show all the projects with some var.`
  <details>
  <summary>e.g.: <i>Circleci - vars with projects</i></summary>
    <pre>
    MATCH(var:CircleCIVar)<-[r:HAS_VAR]-(project:CircleCIProject)
    RETURN var,r,project</pre>
  </details>
</details>

#### Circleci - who can steal $secret
`Show ppals that can steal a secret`

<details>
  <summary>e.g.: <i>Circleci - who can steal AWS_TOKEN</i></summary>
    <pre>
    MATCH(s:CircleCISecret{name:$secret})<-[r:CAN_STEAL_SECRET]-(ppal)
    RETURN s,r,ppal</pre>
  </details>
</details>

#### Circleci - secret stealers
`Show ppals that can steal secrets`

<details>
  <summary>e.g.: <i>Circleci - secret stealers</i></summary>
    <pre>
    MATCH(s:CircleCISecret)<-[r:CAN_STEAL_SECRET]-(ppal)
    RETURN s,r,ppal</pre>
  </details>
</details>

### Projects

<details>
<summary><b>Show queries to search for projects with some special characteristic</b></summary>

#### Circleci - active projects
`Show projects with some worflow in the last 3 months.`
  <details>
  <summary>e.g.: <i>Circleci - active projects</i></summary>
    <pre>
    MATCH(project:CircleCIProject{is_active:True})
    RETURN project</pre>
  </details>
</details>
</details>