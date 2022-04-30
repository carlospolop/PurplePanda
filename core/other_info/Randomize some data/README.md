# Randomize data
Here you can find some cypher queries to randomize some data (this WON'T randomize all the data) to show results.

## Github
- Randomize secrets names
```
MATCH(s:GithubSecret)
SET s.name = apoc.text.random(10, "A-Z0-9.$")
RETURN s.name
```

- Randomize leaks data
```
MATCH(l:GithubLeak)
SET l.name = apoc.text.random(10, "A-Z0-9.$")
RETURN l.name
```

- Randomize CAN_STEAL_SECRET reason
```
MATCH(u)-[r:CAN_STEAL_SECRET]->(s:GithubSecret)
SET r.reason = "can write in repo " + apoc.text.random(10, "A-Z0-9.$")
RETURN r.reason
```

- Randomize repos name
```
MATCH(r:GithubRepo)
SET r.name = apoc.text.random(10, "A-Z0-9.$")
RETURN r.name
```

- Randomize user names
```
MATCH(u:GithubUser)
WHERE u.name <> "carlospolop"
SET u.name = apoc.text.random(10, "A-Z0-9.$")
RETURN u.name
```

- Randomize teams names
```
MATCH(t:GithubTeam)
SET t.name = apoc.text.random(10, "A-Z0-9.$")
RETURN t.name
```

- Randomize organizations names
```
MATCH(o:GithubOrganization)
SET o.name = apoc.text.random(10, "A-Z0-9.$")
RETURN o.name
```

- Randomize full_names
```
MATCH(s:Github)
SET s.full_name = apoc.text.random(10, "A-Z0-9.$")
RETURN s.full_name
```

- Randomize privesc reason
```
MATCH(ppal:GithubPrincipal)-[r:PRIVESC]->(res)
SET r.reasons = ["Can merge in [REPO_NAME] which is mirrored by [MIRROR ADDRESS] which is used by [CLOUD FUNCTION] which run the SA"]
RETURN ppal,r,res
```

## Kubernetes
- Randomize ingresses names
```
MATCH(i:K8sIngress)
SET i.name = apoc.text.random(10, "A-Z0-9.$")
RETURN i.name
```

- Randomize services names
```
MATCH(s:K8sService)
SET s.name = apoc.text.random(10, "A-Z0-9.$")
RETURN s.name
```

- Randomize pods names
```
MATCH(p:K8sPod)
SET p.name = apoc.text.random(10, "A-Z0-9.$")
RETURN p.name
```

- Randomize ppals names
```
MATCH(p:K8sPrincipal)
SET p.name = apoc.text.random(10, "A-Z0-9.$")
RETURN p.name
```

- Randomize namespaces names
```
MATCH(ns:K8sNamespace)
SET ns.name = apoc.text.random(10, "A-Z0-9.$")
RETURN ns.name
```

- Randomize privesc reasons names
```
MATCH(ns:K8sPrincipal)-[r:PRIVESC]->(b)
SET r.reasons = ["The ClusterRole CLUSTERROLE_NAME assigned by the binding BINDINGNAM fullfil the necessary privesc permissions '*' with the set of permissions '*' over the resource '*'."]
RETURN ns.name
```

- Randomize labels
```
MATCH (k:K8s) WHERE EXISTS(k.labels)
SET k.labels = apoc.text.random(10, "A-Z0-9.$")
RETURN k.labels
```

- Randomize annotations
```
MATCH (k:K8s) WHERE EXISTS(k.annotations)
SET k.annotations = apoc.text.random(10, "A-Z0-9.$")
RETURN k.annotations
```

- Randomize annotations
```
MATCH (k:K8s) WHERE EXISTS(k.priorityClassName)
SET k.priorityClassName = apoc.text.random(10, "A-Z0-9.$")
RETURN k.priorityClassName
```

- Randomize annotations
```
MATCH (k:K8s) WHERE EXISTS(k.self_link)
SET k.self_link = apoc.text.random(10, "A-Z0-9.$")
RETURN k.self_link
```

- Randomize interesting_permissions
```
MATCH (k:K8s) WHERE EXISTS(k.interesting_permissions)
SET k.interesting_permissions = ["The ClusterRole 'CLUSTERROLENAME' assigned by the binding 'CRBINDING' fullfil the necessary privesc permissions '*' with the set of permissions '*' over the resource '*'."]
RETURN k.interesting_permissions
```

- Randomize uid
```
MATCH (k:K8s) WHERE EXISTS(k.uid)
SET k.uid = apoc.text.random(10, "A-Z0-9.$")
RETURN k.uid
```

- Randomize ns_name
```
MATCH (k:K8s) WHERE EXISTS(k.ns_name)
SET k.ns_name = apoc.text.random(10, "A-Z0-9.$")
RETURN k.ns_name
```

- Randomize iam_amazonaws_role_arn
```
MATCH (k:K8s) WHERE EXISTS(k.iam_amazonaws_role_arn) AND size(k.iam_amazonaws_role_arn) > 0
SET k.iam_amazonaws_role_arn = "arn:aws:iam::" + apoc.text.random(10, "0-9") + ":role/" + apoc.text.random(10, "A-Z")
RETURN k.iam_amazonaws_role_arn
```


## GCP
```
MATCH (g:Gcp) WHERE EXISTS(g.name)
SET g.name = apoc.text.random(10, "A-Z0-9.$")
RETURN g.name

MATCH (g:Gcp) WHERE EXISTS(g.email)
SET g.email = apoc.text.random(10, "A-Z0-9.$")+"@email.com"
RETURN g.email

MATCH (g:Gcp) WHERE EXISTS(g.domain)
SET g.domain = apoc.text.random(10, "a-z0-9")+".com"
RETURN g.domain

MATCH (g:Gcp) WHERE EXISTS(g.displayName)
SET g.displayName = apoc.text.random(10, "A-Z0-9.$")
RETURN g.displayName

MATCH (g:Gcp) WHERE EXISTS(g.uniqueId)
SET g.uniqueId = apoc.text.random(10, "0-9")
RETURN g.uniqueId

MATCH (g:Gcp) WHERE EXISTS(g.source)
SET g.source = apoc.text.random(10, "A-Z0-9")
RETURN g.source

MATCH (g:Gcp) WHERE EXISTS(g.targetTags)
SET g.targetTags = "https://www.googleapis.com/compute/v1/projects/blahblahblah"
RETURN g.targetTags

MATCH (g:Gcp) WHERE EXISTS(g.projectNumber)
SET g.projectNumber = apoc.text.random(10, "0-9")
RETURN g.projectNumber

MATCH (g:Gcp) WHERE EXISTS(g.description)
SET g.description = apoc.text.random(10, "0-9")
RETURN g.description

MATCH (g:Gcp) WHERE EXISTS(g.interesting_permissions)
SET g.interesting_permissions = apoc.text.regreplace(g.interesting_permissions[0], " over [^ ]+", " over projects/FAKE_PROJECT")
RETURN g.interesting_permissions

MATCH (g:Gcp)-[r:PRIVESC]->(b)
SET r.reasons = apoc.text.regreplace(r.reasons[0], " to .*", " to <RESOURCE NAME>")
RETURN r.reasons

MATCH (g:Gcp)-[r:HAS_ROLE]->(b)
SET r.roles = [apoc.text.regreplace(r.roles[0], "projects/[^/]+/", "")]
RETURN r.roles
```


## Generic

- Randomize publicdomains names
```
MATCH(p:PublicDomain)
SET p.name = apoc.text.random(10, "a-z0-9")+".com"
RETURN p.name
```

- Randomize PublicIP names
```
MATCH(ip:PublicIP)
SET ip.name = apoc.text.random(2, "0-9")+"."+apoc.text.random(2, "0-9")+"."+apoc.text.random(2, "0-9")+"."+apoc.text.random(2, "0-9")
RETURN ip.name
```
