# Investigation

In this section we are going to explain how to use PurplePanda to **find potential problems within your Github organization** and possible **privilege escalation paths from Github to other clouds**.

## Red, Purple & Blue Teams

Searching for **sensitive information in secrets and leaks** is something all the teams should do.

### Secrets & Leaks

*Note that PurplePanda doesn't have the capabilities (yet) to steal the the secrets values automatically because it involves performing writing into the repos, so you can only search by secret name and you will need to steal the secret manually.*


<details>
<summary><b>Show queries to search secrets and leaks</b></summary>

#### Gh - secrets
`Show all the secrets`
  <details>
  <summary>e.g.: <i>Gh - orgs</i></summary>
    <pre>
    MATCH(s:GithubSecret) RETURN s</pre>
  </details>

#### Gh - secrets filtered by $filter
`Show all the secrets filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - secrets filtered by aws</i></summary>
    <pre>
    MATCH(s:GithubSecret)
    WHERE toLower(s.name) CONTAINS toLower($filter) 
    RETURN s</pre>
  </details>
  
#### Gh - leaks
`Show all the leaks`
  <details>
  <summary>e.g.: <i>Gh - leaks</i></summary>
    <pre>
    MATCH(l:GithubLeak) RETURN l</pre>
  </details>

#### Gh - leaks filtered by $filter
`Show all the leaks filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - leaks filtered by aws</i></summary>
    <pre>
    MATCH(l:GithubLeak)
    WHERE toLower(l.name) CONTAINS toLower($filter) 
    RETURN l</pre>
  </details>
</details>

---

## Purple & Blue Teams

In this in this section you can find the queries sugegsted to Purple and Blue teams who wants to **find vulnerable configurations across all the data without any specific starting point**.

### Secrets

<details>
<summary><b>Show queries to search potential secrets stealers</b></summary>

#### Gh - $secret stealers
`Show all the users that can steal the secret`

  <details>
  <summary>e.g.: <i>Gh - TOKEN_API_AWS stealers</i></summary>
    <pre>
    MATCH(s:GithubSecret {name:$secret})<-[r:CAN_STEAL_SECRET]-(u:Github)
    RETURN s,r,u</pre>
  </details>
</details>

### Organizations

<details>
<summary><b>Show queries to search organization admins</b></summary>

#### Gh - org admins
`Show all the admins in the Github Organizations`

  <details>
  <summary>e.g.: <i>Gh - org admins</i></summary>
    <pre>
    MATCH (o:GithubOrganization)-[r:PART_OF {membership:"admin"}]-(u) RETURN u,r,o</pre>
  </details>
</details>

### Repos

<details>
<summary><b>Show queries to search people that can merge in repos</b></summary>

#### Gh - mergers of $repo
`Show all principals that can merge in default master branch of the repo on their own`

<details>
  <summary>e.g.: <i>Gh - mergers of repo_name</i></summary>
    <pre>
    MATCH(repo:GithubRepo{name:$repo})-[r:HAS_BRANCH]->(b:GithubBranch)<-[r2:CAN_MERGE]-(u:Github)
    RETURN repo,r,b,r2,u</pre>
</details>

#### Gh - ppals can merge in mirrored repos
`Show all the principals with merge access to mirrored repos`

<details>
  <summary>e.g.: <i>Gh - ppals can merge in mirrored repos</i></summary>
    <pre>
    MATCH (ppal)-[r3:CAN_MERGE]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)<-[r1:IS_MIRROR]-(resource)    
    RETURN ppal,r3,b,r2,repo,r1,resource</pre>
  </details>
</details>

### Teams

<details>
<summary><b>Show queries to search teams that can merge in repos</b></summary>

#### Gh - teams that can merge
`Show all branches and repos where teams can merge code alone`

  <details>
  <summary>e.g.: <i>Gh - teams that can merge</i></summary>
    <pre>
    MATCH(t:GithubTeam)-[r1:CAN_MERGE]-(b:GithubBranch)-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN t,r1,b,r2,repo</pre>
  </details>
</details>

### Privilege Escalation

<details>
<summary><b>Show queries to search github principals that can escalate privileges into other clouds</b></summary>

#### Gh - ppals that can privesc
`Show all the github principals that can escalate privileges into other clouds`

  <details>
  <summary>e.g.: <i>Gh - ppals that can privesc</i></summary>
    <pre>
    MATCH(ppal:GithubPrincipal)-[r:PRIVESC]->(res)
    RETURN ppal,r,res</pre>
  </details>
</details>

---

## Red Teams

Usually Red Teams will **compromise a few set of credentials** and they will be interested in knowing how to **escalate privileges from there**. Therefore, the following queries are going to be similar to the ones of the Purple & Blue Teams sections but **having an account as starting point**.

### Organizations

<details>
<summary><b>Show queries to search the organizations you are an admin</b></summary>

#### Gh - $user admin orgs
`Show all the orgs where a user is admin`

<details>
  <summary>e.g.: <i>Gh - carlospolop admin orgs</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:PART_OF{membership:"admin"}]->(o:GithubOrganization)
    RETURN u,r,o</pre>
  </details>
</details>

### Secrets

<details>
<summary><b>Show queries to search the secrets you can steal</b></summary>

#### Gh - secrets $user can steal
`Show all secrets that a user can steal`

<details>
  <summary>e.g.: <i>Gh - secrets carlospolop can steal</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:CAN_STEAL_SECRET]->(s:GithubSecret)
    RETURN u,r,s</pre>
  </details>
</details>

### Repos

<details>
<summary><b>Show queries to search the repos you can merge into</b></summary>

#### Gh - repos $user can merge
`Show all branches and repos where a user can merge on his own`

<details>
  <summary>e.g.: <i>Gh - repos carlospolop can merge</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r1:CAN_MERGE]->(s:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN u,r1,s,r2,repo</pre>
  </details>
</details>

### Privilege Escalation

<details>
<summary><b>Show queries to search how a github principal can escalate privileges into other clouds</b></summary>

#### Gh - $ppal privesc
`Show all the paths a github principal (user or team) can escalate privileges into other clouds`

  <details>
  <summary>e.g.: <i>Gh - carlospolop privesc</i></summary>
    <pre>
    MATCH(ppal:GithubPrincipal{name:$ppal})-[r:PRIVESC]->(res)
    RETURN ppal,r,res</pre>
  </details>

#### Gh - mirrored repos $ppal can merge
`Show all branches of mirrored repos where a principal can merge on his own`

<details>
  <summary>e.g.: <i>Gh - mirrored repos carlospolop can merge</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$ppal})-[r1:CAN_MERGE]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)<-[r3:IS_MIRROR]-(s)
    RETURN u,r1,b,r2,repo,r3,s</pre>
    </details>
</details>