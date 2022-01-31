# Predefined Searches

## Privilege Escalation

<details>
<summary>Details</summary>

### Gh - ppals that can privesc
`Show all the github principals that can escalate privileges into other clouds`

  <details>
  <summary>e.g.: <i>Gh - ppals that can privesc</i></summary>
    <pre>
    MATCH(ppal:GithubPrincipal)-[r:PRIVESC]->(res)
    RETURN ppal,r,res</pre>
  </details>

### Gh - $ppal privesc
`Show all the paths a github principal (user or team) can escalate privileges into other clouds`

  <details>
  <summary>e.g.: <i>Gh - carlospolop privesc</i></summary>
    <pre>
    MATCH(ppal:GithubPrincipal{name:$ppal})-[r:PRIVESC]->(res)
    RETURN ppal,r,res</pre>
  </details>
</details>

---

## Organizations

<details>
<summary>Details</summary>

### Gh - orgs
`Show all the organizations`
  <details>
  <summary>e.g.: <i>Gh - orgs</i></summary>
    <pre>
    MATCH(o:GithubOrganization) RETURN o</pre>
  </details>

### Gh - orgs filtered by $filter
`Show all the principals filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - orgs filtered by org_name</i></summary>
    <pre>
    MATCH(o:GithubOrganization)
    WHERE toLower(o.name) CONTAINS toLower($filter) 
    RETURN o</pre>
  </details>

### Gh - org admins
`Show all the admins in the Github Organizations`

  <details>
  <summary>e.g.: <i>Gh - org admins</i></summary>
    <pre>
    MATCH (o:GithubOrganization)-[r:PART_OF {membership:"admin"}]-(u) RETURN u,r,o</pre>
  </details>


### Gh - org secrets
`Show all the secrets declared for the Organization. Note that due to lack of permissions there might be organization level secrets that aren't showed here. They might me showed in the next section`

  <details>
  <summary>e.g.: <i>Gh - org secrets</i></summary>
    <pre>
    MATCH(s:GithubSecret)<-[r:USES_SECRET]-(o:GithubOrganization) 
    RETURN s,r,o</pre>
  </details>
</details>

---

## Secrets & Leaks

<details>
<summary>Details</summary>

### Gh - secrets
`Show all the secrets`
  <details>
  <summary>e.g.: <i>Gh - orgs</i></summary>
    <pre>
    MATCH(s:GithubSecret) RETURN s</pre>
  </details>

### Gh - secrets filtered by $filter
`Show all the secrets filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - secrets filtered by aws</i></summary>
    <pre>
    MATCH(s:GithubSecret)
    WHERE toLower(s.name) CONTAINS toLower($filter) 
    RETURN s</pre>
  </details>
  
### Gh - leaks
`Show all the leaks`
  <details>
  <summary>e.g.: <i>Gh - leaks</i></summary>
    <pre>
    MATCH(l:GithubLeak) RETURN l</pre>
  </details>

### Gh - leaks filtered by $filter
`Show all the leaks filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - leaks filtered by aws</i></summary>
    <pre>
    MATCH(l:GithubLeak)
    WHERE toLower(l.name) CONTAINS toLower($filter) 
    RETURN l</pre>
  </details>

### Gh - $secret stealers
`Show all the users that can steal the secret`

  <details>
  <summary>e.g.: <i>Gh - TOKEN_API_AWS stealers</i></summary>
    <pre>
    MATCH(s:GithubSecret {name:$secret})-[r:CAN_STEAL_SECRET]-(u:Github)
    RETURN s,r,u</pre>
  </details>
</details>
</details>

---

## Repos
 
<details>
<summary>Details</summary>

### Gh - repos
`Show all the repos`
  <details>
  <summary>e.g.: <i>Gh - repos</i></summary>
    <pre>
    MATCH(repo:GithubRepo) RETURN repo</pre>
  </details>

### Gh - repos filtered by $filter
`Show all the repos filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - repos filtered by aws</i></summary>
    <pre>
    MATCH(repo:GithubRepo)
    WHERE toLower(repo.name) CONTAINS toLower($filter) 
    RETURN repo</pre>
  </details>
    
### Gh - repos using secret containing $filter
`Show all the repos that are using a secret containing $filter in its name (not case sensitive)`

  <details>
  <summary>e.g.: <i>Gh - repos with secret containing token</i></summary>
    <pre>
    MATCH(s:GithubSecret) WHERE toLower(s.name) CONTAINS toLower($filter) 
    MATCH(s)<-[r:USES_SECRET]-(repo:GithubRepo)
    RETURN repo,r,s</pre>
  </details>

### Gh - repos with leak containing $filter
`Show all the repos that have a leak containing $filter (not case sensitive)`

  <details>
  <summary>e.g.: <i>Gh - repos with leak containing token</i></summary>
    <pre>
    MATCH(l:GithubLeak) WHERE toLower(l.name) CONTAINS toLower($filter) 
    MATCH(l)-[r:PART_OF]->(repo:GithubRepo)
    RETURN repo,r,l</pre>
  </details>

### Gh - admins of $repo
`Show all admins of the indicated repo`

<details>
  <summary>e.g.: <i>Gh - admins of repo_name</i></summary>
    <pre>
    MATCH(repo:GithubRepo{name:$repo})<-[r:HAS_PERMS{admin:True}]-(u:Github)
    RETURN repo,r,u</pre>
  </details>

### Gh - writers of $repo
`Show all principals with write permission over the indicated repo`

<details>
  <summary>e.g.: <i>Gh - writers of repo_name</i></summary>
    <pre>
    MATCH(repo:GithubRepo{name:$repo})<-[r:HAS_PERMS]-(u:Github)
    WHERE r.admin = True OR r.maintain = True OR r.push = True
    RETURN repo,r,u</pre>
  </details>

#### Gh - mergers of $repo
`Show all principals that can merge in default master branch of the repo on their own`

<details>
  <summary>e.g.: <i>Gh - mergers of repo_name</i></summary>
    <pre>
    MATCH(repo:GithubRepo{name:$repo})-[r:HAS_BRANCH]-(b:GithubBranch)-[r2:CAN_MERGE]-(u:Github)
    RETURN repo,r,b,r2,u</pre>
</details>

### Gh - dimissers of $repo
`Show all principals that can dismiss in default master branch of the repo`

  <details>
  <summary>e.g.: <i>Gh - dimissers of $repo</i></summary>
    <pre>
    MATCH(repo:GithubRepo{name:$repo})-[r1:HAS_BRANCH]->(b:GithubBranch)<-[r2:CAN_DISMISS]-(u:Github)
    RETURN repo,r1,b,r2,u</pre>
  </details>

### Gh - repos with missconfigured codeowners
`Show all the repos with unknown or empty codeowners`

<details>
  <summary>e.g.: <i>Gh - repos with missconfigured codeowners</i></summary>
    <pre>
    MATCH(repo:GithubRepo) WHERE repo.unkown_codeowners <> [] OR repo.no_codeowners
    RETURN repo</pre>
  </details>

### Gh - ppals can merge in mirrored repos
`Show all the principals with merge access to mirrored repos`

<details>
  <summary>e.g.: <i>Gh - ppals can merge in mirrored repos</i></summary>
    <pre>
    MATCH (s)-[r1:IS_MIRROR]->(repo:GithubRepo)-[r2:HAS_BRANCH]->(b:GithubBranch)<-[r3:CAN_MERGE]-(ppal:GithubPrincipal)
    RETURN s,r1,repo,r2,b,r3,ppal</pre>
  </details>
</details>

---

## Users

<details>
<summary>Details</summary>

### Gh - users
`Show all the users`
  <details>
  <summary>e.g.: <i>Gh - orgs</i></summary>
  <pre>
  MATCH(u:GithubUser) RETURN u</pre>
  </details>

### Gh - users filtered by $filter
`Show all the users filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - users filtered by carlos</i></summary>
    <pre>
    MATCH(u:GithubUser)
    WHERE toLower(u.name) CONTAINS toLower($filter) 
    RETURN u</pre>
  </details>

### Gh - $user admin orgs
`Show all the orgs where a user is admin`

<details>
  <summary>e.g.: <i>Gh - carlospolop admin orgs</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:PART_OF{membership:"admin"}]->(o:GithubOrganization)
    RETURN u,r,o</pre>
  </details>

### Gh - $user admin repos
`Show all the repos where a user is admin`

<details>
  <summary>e.g.: <i>Gh - carlospolop admin repos</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:HAS_PERMS{admin:True}]-(repo:GithubRepo)
    RETURN u,r,repo</pre>
  </details>

### Gh - secrets $user can steal
`Show all secrets that a user can steal`

<details>
  <summary>e.g.: <i>Gh - secrets carlospolop can steal</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:CAN_STEAL_SECRET]->(s:GithubSecret)
    RETURN u,r,s</pre>
  </details>

### Gh - repos $user can merge
`Show all branches and repos where a user can merge on his own`

<details>
  <summary>e.g.: <i>Gh - repos carlospolop can merge</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r1:CAN_MERGE]->(s:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN u,r1,s,r2,repo</pre>
  </details>

### Gh - mirrored repos $user can merge
`Show all branches of mirrored repos where a user can merge on his own`

<details>
  <summary>e.g.: <i>Gh - mirrored repos carlospolop can merge</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r1:CAN_MERGE]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)<-[r3:IS_MIRROR]-(s)
    RETURN u,r1,b,r2,repo,r3,s</pre>
  </details>

### Gh - selfhosted runners $user can run
`Show all selfhosted runners a user can run`

<details>
  <summary>e.g.: <i>Gh - selfhosted runners carlospolop can run</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:CAN_RUN]->(shr:GithubSelfHostedRunner)
    RETURN u,r,shr</pre>
  </details>

### Gh - repos $user can write
`Show all branches and repos where a user can merge code alone`

<details>
  <summary>e.g.: <i>Gh - repos carlospolop can write</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r:HAS_PERMS]->(repo:GithubRepo)
    WHERE r.admin = True OR r.maintain = True OR r.push = True
    RETURN u,r,repo</pre>
  </details>

### Gh - repos $user can dismiss
`Show all branches and repos where a user can dismiss`

  <details>
  <summary>e.g.: <i>Gh - repos carlospolop can dismiss</i></summary>
    <pre>
    MATCH(u:GithubUser{name:$user})-[r1:CAN_DISMISS]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN u,r1,b,r2,repo</pre>
  </details>
</details>

---

## Teams

<details>
<summary>Details</summary>

*A team cannot be organization admin.*

### Gh - teams
`Show all the teams`
  <details>
  <summary>e.g.: <i>Gh - orgs</i></summary>
    <pre>
    MATCH(t:GithubTeam) RETURN t</pre>
  </details>

### Gh - teams filtered by $filter
`Show all the teams filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>Gh - teams filtered by carlos</i></summary>
    <pre>
    MATCH(t:GithubTeam)
    WHERE toLower(t.name) CONTAINS toLower($filter) 
    RETURN t</pre>
  </details>

### Gh - $team admin repos
`Show all teams that are repo admins`

  <details>
  <summary>e.g.: <i>Gh - team_name admin repos</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$team})-[r:HAS_PERMS{admin:True}]->(repo:GithubRepo)
    RETURN t,r,repo</pre>
  </details>

### Gh - secrets $team can steal
`Show all secrets that a team can steal`

  <details>
  <summary>e.g.: <i>Gh - secrets team_name can steal</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$team})-[r:CAN_STEAL_SECRET]->(s:GithubSecret)
    RETURN t,r,s</pre>
  </details>

### Gh - teams that can merge
`Show all branches and repos where teams can merge code alone`

  <details>
  <summary>e.g.: <i>Gh - teams that can merge</i></summary>
    <pre>
    MATCH(t:GithubTeam)-[r1:CAN_MERGE]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN t,r1,b,r2,repo</pre>
  </details>

### Gh - repos $team can merge
`Show all branches and repos where a team can merge code alone`

  <details>
  <summary>e.g.: <i>Gh - repos team_name can merge</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$team})-[r1:CAN_MERGE]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN t,r1,b,r2,repo</pre>
  </details>

### Gh - mirrored repos $team can merge
`Show all branches of mirrored repos where a team can merge on his own`

<details>
  <summary>e.g.: <i>Gh - mirrored repos team_name can merge</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$user})-[r1:CAN_MERGE]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)<-[r3:IS_MIRROR]-(s)
    RETURN t,r1,b,r2,repo,r3,s</pre>
  </details>

### Gh - selfhostedrunners $team can run
`Show all selfhosted runners a team can run`

  <details>
  <summary>e.g.: <i>Gh - selfhostedrunners team_name can run</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$team})-[r:CAN_RUN]->(shr:GithubSelfHostedRunner)
    RETURN t,r,shr</pre>
  </details>

### Gh - repos $team can write
`Show all branches and repos where a team can write`

  <details>
  <summary>e.g.: <i>Gh - repos team_name can write</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$team})-[r:HAS_PERMS]->(repo:GithubRepo)
    WHERE r.admin = True OR r.maintain = True OR r.push = True
    RETURN t,r,repo</pre>
  </details>

### Gh - repos $team can dismiss
`Show all branches and repos where a team can dismiss`

  <details>
  <summary>e.g.: <i>Gh - repos team_name can dismiss</i></summary>
    <pre>
    MATCH(t:GithubTeam{name:$team})-[r1:CAN_DISMISS]->(b:GithubBranch)<-[r2:HAS_BRANCH]-(repo:GithubRepo)
    RETURN t,r1,b,r2,repo</pre>
  </details>
</details>
</details>