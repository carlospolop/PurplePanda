# Investigation

In this section we are going to explain how to use PurplePanda to **find potential problems within your concourse environmentr** and possible **privilege escalation paths from concourse to other clouds**.

## Red, Purple & Blue Teams

Searching for **sensitive information in secrets and declared params** is something all the teams should do.
Moreover, checking who has **access as member, owner or admin** is also very important.

### Secrets

*You need to have enough permissions to retreive the secrets.*

<details>
<summary><b>Show queries to search secrets as, if stolen, it's higly probable that they contain sensitive information</b></summary>

#### Councourse - secrets
`Show all the secrets.`
  <details>
  <summary>e.g.: <i>Councourse - secrets</i></summary>
    <pre>
    MATCH(secret:ConcourseSecret)
    RETURN secret</pre>
  </details>

#### Councourse - secrets with pipelines
`Show all the secrets with their related pipelines.`
  <details>
  <summary>e.g.: <i>Councourse - secrets with pipelines</i></summary>
    <pre>
    MATCH(secret:ConcourseSecret)<-[r:HAS_SECRET]-(pipeline:ConcoursePipeline)
    RETURN secret,r,pipeline</pre>
  </details>
</details>

### Params

<details>
<summary><b>Show plans with params or vars defined as they might contain sensitive information</b></summary>

#### Concourse - params
`Show all the plans with some param or var declared.`
  <details>
  <summary>e.g.: <i>K8s - envars with value</i></summary>
    <pre>
    MATCH(plan:ConcoursePlan) WHERE ((plan.params IS NOT NULL AND plan.params <> "null") OR (plan.runparams IS NOT NULL AND plan.runparams <> "null") OR (plan.vars IS NOT NULL AND plan.vars <> "null"))
    RETURN plan.name,plan.params,plan.runparams,plan.vars</pre>
  </details>
</details>

### Principals

<details>
<summary><b>Show all the principals and their roles</b></summary>

#### Concourse - ppals
`Show all the principals in concourse`
  <details>
  <summary>e.g.: <i>Concourse - Ppals</i></summary>
    <pre>
    MATCH(team:ConcourseTeam)<-[r:HAS_ROLE]-(ppal:ConcoursePrincipal)
    RETURN team,r,ppal</pre>
  </details>

#### K8s - privileged ppals
`Show only the privileged principals`
  <details>
  <summary>e.g.: <i>K8s - privileged ppals</i></summary>
    <pre>
    MATCH(team:ConcourseTeam)<-[r:HAS_ROLE]-(ppal:ConcoursePrincipal)
    WHERE r.role <> "viewer" and r.role <> "pipeline-operator"
    RETURN team,r,ppal</pre>
  </details>
</details>
</details>