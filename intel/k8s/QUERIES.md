# Predefined Searches

## K8s Generic

<details>
<summary>Details</summary>

### K8s - k8s filtered by $filter
`Show all the K8s objects filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - k8s filtered by something</i></summary>
    <pre>
    MATCH(n:K8s)
    WHERE toLower(n.name) CONTAINS toLower($filter) 
    RETURN n</pre>
  </details>

### K8s - k8s tiller
`Show all the K8s objects related to tiller`
  <details>
  <summary>e.g.: <i>K8s - k8s tiller</i></summary>
    <pre>
    MATCH(k:K8s)
    WHERE toLower(k.name) CONTAINS toLower("tiller") 
    RETURN k</pre>
  </details>
</details>

---

## Namespaces

<details>
<summary>Details</summary>

### K8s - namespaces
`Show all the namespaces`
  <details>
  <summary>e.g.: <i>K8s - namespaces</i></summary>
    <pre>
    MATCH(n:K8sNamespace) RETURN n</pre>
  </details>

### K8s - namespaces filtered by $filter
`Show all the namespaces filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - namespaces filtered by default</i></summary>
    <pre>
    MATCH(n:K8sNamespace)
    WHERE toLower(n.name) CONTAINS toLower($filter) 
    RETURN n</pre>
  </details>

### K8s - namespaces with iam roles
`Show all the namespaces with permitted AWS IAM roles`
  <details>
  <summary>e.g.: <i>K8s - namespaces with iam roles</i></summary>
    <pre>
    MATCH(n:K8sNamespace)
    WHERE n.iam_amazonaws_com_permitted <> ""
    RETURN n</pre>
  </details>
</details>

---

## Secrets

<details>
<summary>Details</summary>

### K8s - secrets
`Show all the secrets`
  <details>
  <summary>e.g.: <i>K8s - secrets</i></summary>
    <pre>
    MATCH(s:K8sSecret) RETURN s</pre>
  </details>

### K8s - secrets with name filtered by $filter
`Show all the secrets whose name contains $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - secrets filtered by token</i></summary>
    <pre>
    MATCH(s:K8sSecret)
    WHERE toLower(s.name) CONTAINS toLower($filter) 
    RETURN s</pre>
  </details>

### K8s - secrets with value filtered by $filter
`Show all the secrets whose name contains $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - secrets with value filtered by AI</i></summary>
    <pre>
    MATCH(s:K8sSecret)
    WHERE any(text in s.values_cleartext WHERE text CONTAINS $filter) 
    RETURN s</pre>
  </details>

### K8s - secrets in $name
`Show all the secrets related to a name (it can be a namespace, pod...)`
  <details>
  <summary>e.g.: <i>K8s - secrets in kube-system</i></summary>
    <pre>
    MATCH(s:K8sSecret)-[r]-(k:K8s{name:$name})
    RETURN s,r,k</pre>
  </details>

### K8s - secrets with values
`Show all the secrets with values discovered`
  <details>
  <summary>e.g.: <i>K8s - secrets with values</i></summary>
    <pre>
    MATCH(s:K8sSecret)
    WHERE s.values <> []
    RETURN s</pre>
  </details>
</details>

---

## Nodes

<details>
<summary>Details</summary>

### K8s - nodes
`Show all the nodes`
  <details>
  <summary>e.g.: <i>K8s - nodes</i></summary>
    <pre>
    MATCH(n:K8sNode) RETURN n</pre>
  </details>

### K8s - nodes filtered by $filter
`Show all the nodes filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - nodes filtered by node_name</i></summary>
    <pre>
    MATCH(n:K8sNode)
    WHERE toLower(n.name) CONTAINS toLower($filter) 
    RETURN n</pre>
  </details>

### K8s - master nodes
`Show all the nodes with role master`
  <details>
  <summary>e.g.: <i>K8s - master nodes</i></summary>
    <pre>
    MATCH(n:K8sNode)
    WHERE n.role == "master"
    RETURN n</pre>
  </details>
</details>

---

## Pods

<details>
<summary>Details</summary>

### K8s - pods
`Show all the pods`
  <details>
  <summary>e.g.: <i>K8s - pods</i></summary>
    <pre>
    MATCH(p:K8sPod) RETURN p</pre>
  </details>

### K8s - pods filtered by $filter
`Show all the pods filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - pods filtered by super_pod</i></summary>
    <pre>
    MATCH(p:K8sPod)
    WHERE toLower(p.name) CONTAINS toLower($filter) 
    RETURN p</pre>
  </details>

### K8s - pods with iam role
`Show all the pods with iam role`
  <details>
  <summary>e.g.: <i>K8s - pods with iam role</i></summary>
    <pre>
    MATCH(p:K8sPod)
    WHERE p.iam_amazonaws_com_role <> ""
    RETURN p</pre>
  </details>

### K8s - priv pods
```
Show all the potential privileged pods:
- runAsUser == 0
- runAsNonRoot != True and runAsUser == ""
- runAsGroup < 50
- any group in supplementaryGroups < 50
- host_network == True
- host_pid == True
- host_ipc == True
- host_path == True and any of ['/', '/proc', '/sys', '/dev', '/var/run', 'docker.sock', 'crio.sock', '/kubelet', '/pki', '/home/admin', '/etc', '/kubernetes', '/manifests', '/root']
```
  <details>
  <summary>e.g.: <i>K8s - root pods</i></summary>
    <pre>
    MATCH(p:K8sPod)
    WHERE p.sc_runAsUser = 0 OR 
    p.sc_runAsNonRoot <> True AND p.sc_runAsUser = "" OR
    p.sc_runAsGroup < 50 OR
    any(grp in p.sc_supplemental_groups WHERE grp < 50) OR
    p.host_network OR
    p.host_pid OR
    p.host_ipc OR
    any(path IN p.host_path WHERE any( regex IN ["/", "/proc.*", "/sys.*", "/dev.*", "/var/run.*", ".*docker.sock", ".*crio.sock", ".*/kubelet.*", ".*/pki.*", "/home/admin.*", "/etc.*", ".*/kubernetes.*", ".*/manifests.*", "/root.*"] WHERE regex =~ path ))
    RETURN p</pre>
  </details>

### K8s - pods using secret $filter
`Show all the pods using a secret containing in its name $filter (no case sensitive)`
  <details>
  <summary>e.g.: <i>K8s - pods using secret token</i></summary>
    <pre>
    MATCH(s:K8sSecret) WHERE toLower(s.name) CONTAINS toLower($filter)
    MATCH(s)-[r:USE_SECRET]-(p:K8sPod)
    RETURN s,r,p</pre>
  </details>
</details>

---

## Containers

<details>
<summary>Details</summary>

### K8s - containers
`Show all the containers`
  <details>
  <summary>e.g.: <i>K8s - containers</i></summary>
    <pre>
    MATCH(c:K8sContainer) RETURN c</pre>
  </details>

### K8s - containers filtered by $filter
`Show all the containers filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - containers filtered by $filter</i></summary>
    <pre>
    MATCH(c:K8sContainer)
    WHERE toLower(c.name) CONTAINS toLower($filter) 
    RETURN c</pre>
  </details>

### K8s - priv containers
```
Show all the potential privileged pods:
- runAsUser == 0
- runAsNonRoot != True and (runAsUser == "" or runAsUser == 0)
- runAsGroup < 50
- allowPrivilegeEscalation is True
- privileged is True
- some capability is added
```
  <details>
  <summary>e.g.: <i>K8s - privileged containers</i></summary>
    <pre>
    MATCH(p:K8sContainer)
    WHERE p.sc_privileged = True OR
    size(p.sc_capabilities_add) > 0 OR
    .sc_runAsUser = 0 OR 
    p.sc_runAsNonRoot <> True AND (p.sc_runAsUser = "" OR p.sc_runAsUser = 0) OR
    p.sc_runAsGroup < 50 OR
    p.sc_allowPrivilegeEscalation = True
    RETURN p</pre>
  </details>
</details>

---

## Environment variables

<details>
<summary>Details</summary>

### K8s - envars
`Show all the environment variables`
  <details>
  <summary>e.g.: <i>K8s - envars</i></summary>
    <pre>
    MATCH(e:K8sEnvVar) RETURN e</pre>
  </details>

#### K8s - envars with value
`Show all the environment variables with a value not being a secret`
  <details>
  <summary>e.g.: <i>K8s - envars with value</i></summary>
    <pre>
    MATCH(e:K8sEnvVar)-[r:USE_ENV_VAR]-(c:K8sContainer)
    WHERE not r.value =~ '^secret:'
    RETURN e,r,c</pre>
  </details>

#### K8s - with name filtered by $filter
`Show all the envars filtered by $filter`
  <details>
  <summary>e.g.: <i>K8s - with name filtered by aws</i></summary>
    <pre>
    MATCH(e:K8sEnvVar)
    WHERE toLower(e.name) CONTAINS toLower($filter) 
    RETURN e</pre>
  </details>
</details>

---

## Principals

<details>
<summary>Details</summary>

*Principals group is the are the service accounts, users and groups together*

### K8s - ppals
`Show all the principals`
  <details>
  <summary>e.g.: <i>K8s - ppals</i></summary>
    <pre>
    MATCH(p:K8sPrincipal) RETURN p</pre>
  </details>

### K8s - ppals filtered by $filter
`Show all the principals filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - ppals filtered by carlospolop</i></summary>
    <pre>
    MATCH(p:K8sPrincipal)
    WHERE toLower(p.name) CONTAINS toLower($filter) 
    RETURN p</pre>
  </details>

### K8s - ppals that can escape
`Show all the principals that can potentially escape to the Node`
  <details>
  <summary>e.g.: <i>ppals that can escape</i></summary>
    <pre>
    MATCH(p:K8sPrincipal{potential_escape_to_node:True})
    RETURN p</pre>
  </details>

### K8s - paths to escape from $ppal with depth $depth
`Show the path to escape to a Node from the principal $ppal`
  <details>
  <summary>e.g.: <i>K8s - paths to escape from carlospolop with depth 1</i></summary>
    <pre>
    MATCH r = (p:K8sPrincipal{name:$ppal})-[:PRIVESC*..$depth]->(k:K8sPrincipal{potential_escape_to_node: True})
    WITH *, relationships(r) as privescs
    RETURN p,privescs,k</pre>
  </details>

### K8s - paths from $ppal1 to $ppal2 with depth $depth
`Show the path from the principal $ppal1 to the principal $ppal2`
  <details>
  <summary>e.g.: <i>K8s - paths from carlospolop to manolito with depth 2</i></summary>
    <pre>
    MATCH r = (p1:K8sPrincipal{name:$ppal1})-[:PRIVESC*..$depth]-(p2:K8sPrincipal{name:$ppal2})
    WITH *, relationships(r) as privescs
    RETURN p1,privescs,p2</pre>
  </details>

### K8s - $ppal privesc with depth $depth
`Show the privilege escalation path of the indicated ppal`
  <details>
  <summary>e.g.: <i>K8s - carlospolop privesc with depth 3</i></summary>
    <pre>
    MATCH r = (ppal:K8sPrincipal{name:$ppal})-[:PRIVESC*..]->(b)
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,b</pre>
  </details>

### K8s - $ppal iam privesc with depth $depth
`Show the privilege escalation path of the indicated ppal to a Pod with AWS IAM role`
  <details>
  <summary>e.g.: <i>K8s - carlospolop iam privesc with depth 2</i></summary>
    <pre>
    MATCH r = (ppal:K8sPrincipal{name:$ppal})-[:PRIVESC*..$depth]->(p:K8sPod) WHERE p.iam_amazonaws_com_role <> ""
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,p</pre>
  </details>

### K8s - $ppal gcp privesc with depth $depth
`Show the privilege escalation path of the indicated ppal`
  <details>
  <summary>e.g.: <i>K8s - carlospolop privesc with depth 2</i></summary>
    <pre>
    MATCH r = (ppal:K8sPrincipal{name:$ppal})-[:PRIVESC*..$depth]->(ppal2:K8sPrincipal)-[:HAS_CLOUD_PERMS]-(gcp_sa:GcpServiceAccount)
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,ppal2,gcp_sa</pre>
  </details>
</details>

---

## Service Accounts

<details>
<summary>Details</summary>

### K8s - sas
`Show all the service accounts`
  <details>
  <summary>e.g.: <i>K8s - sas</i></summary>
    <pre>
    MATCH(sa:K8sServiceAccount) RETURN sa</pre>
  </details>

### K8s - sas filtered by $filter
`Show all the service accounts filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - sas filtered by $filter</i></summary>
    <pre>
    MATCH(sa:K8sServiceAccount)
    WHERE toLower(sa.name) CONTAINS toLower($filter) 
    RETURN sa</pre>
  </details>

### K8s - sas inside $ns
`Show all the service accounts inside the namespace $ns`
  <details>
  <summary>e.g.: <i>K8s - sas inside $ns</i></summary>
    <pre>
    MATCH (ns:K8sNamespace{name:$ns})-[r:PART_OF]-(sa:K8sServiceAccount)
    RETURN ns,r,sa</pre>
  </details>
</details>

---

## Users

<details>
<summary>Details</summary>

### K8s - users
`Show all the users`
  <details>
  <summary>e.g.: <i>K8s - users</i></summary>
    <pre>
    MATCH(u:K8sUser) RETURN u</pre>
  </details>

### K8s - users filtered by $filter
`Show all the users filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - users filtered by carlospolop</i></summary>
    <pre>
    MATCH(u:K8sUser)
    WHERE toLower(u.name) CONTAINS toLower($filter) 
    RETURN u</pre>
  </details>
</details>

---

## Groups

<details>
<summary>Details</summary>

### K8s - groups
`Show all the groups`
  <details>
  <summary>e.g.: <i>K8s - groups</i></summary>
    <pre>
    MATCH(g:K8sGroup) RETURN g</pre>
  </details>

### K8s - groups filtered by $filter
`Show all the groups filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - groups filtered by admin</i></summary>
    <pre>
    MATCH(g:K8sGroup)
    WHERE toLower(g.name) CONTAINS toLower($filter) 
    RETURN g</pre>
  </details>

### K8s - unauthenticated users access
`Show the unauthenticated group access (system:unauthenticated)`
  <details>
  <summary>e.g.: <i>K8s - unauthenticated users access</i></summary>
    <pre>
    MATCH (g:K8sGroup{name:"system:unauthenticated"})-[r:HAS_PERMS]->(b)
    RETURN g,r,b</pre>
  </details>
</details>

---

## Roles & ClusterRoles

<details>
<summary>Details</summary>

### K8s - roles
`Show all the roles`
  <details>
  <summary>e.g.: <i>K8s - roles</i></summary>
    <pre>
    MATCH(r:K8sRole) RETURN r</pre>
  </details>

### K8s - clusterroles
`Show all the ClusterRoles`
  <details>
  <summary>e.g.: <i>K8s - clusterroles</i></summary>
    <pre>
    MATCH(cr:K8sClusterRole) RETURN cr</pre>
  </details>

### K8s - roles filtered by $filter
`Show all the Roles and ClusterRoles filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - roles filtered by $filter</i></summary>
    <pre>
    OPTIONAL MATCH(r:K8sRole)
    WHERE toLower(r.name) CONTAINS toLower($filter) 
    WITH r
    OPTIONAL MATCH(cr:K8sClusterRole)
    WHERE toLower(cr.name) CONTAINS toLower($filter) 
    RETURN r,cr</pre>
  </details>
</details>

---

## Services

<details>
<summary>Details</summary>

### K8s - svcs
`Show all the services`
  <details>
  <summary>e.g.: <i>K8s - svcs</i></summary>
    <pre>
    MATCH(svc:K8sService) RETURN svc</pre>
  </details>

### K8s - svcs filtered by $filter
`Show all the services filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - svcs filtered by $filter</i></summary>
    <pre>
    MATCH(svc:K8sService)
    WHERE toLower(svc.name) CONTAINS toLower($filter) 
    RETURN svc</pre>
  </details>

### K8s - exposed svcs
`Show all the services with a external IP or domain`
  <details>
  <summary>e.g.: <i>K8s - exposed svcs</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[r1:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[r2:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    RETURN svc1,r1,ip,svc2,r2,dom</pre>
  </details>

### K8s - unused svcs
`Show all the services that aren't related to any Pod`
  <details>
  <summary>e.g.: <i>K8s - unused svcs</i></summary>
    <pre>
    OPTIONAL MATCH (svc:K8sService)
    WHERE NOT EXISTS((svc)-[:HAS_SERVICE]-(:K8sPod))
    RETURN svc</pre>
  </details>
</details>

---

## Ingresses

<details>
<summary>Details</summary>

### K8s - ingresses
`Show all the ingresses`
  <details>
  <summary>e.g.: <i>K8s - ingresses</i></summary>
    <pre>
    MATCH(i:K8sIngress) RETURN i</pre>
  </details>

### K8s - ingresses filtered by $filter
`Show all the ingresses filtered by $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - ingresses filtered by $filter</i></summary>
    <pre>
    MATCH(i:K8sIngress)
    WHERE toLower(i.name) CONTAINS toLower($filter) 
    RETURN i</pre>
  </details>

### K8s - exposed svcs and ingresses
`Show all the services with an external IP or domain and all the ingresses`
  <details>
  <summary>e.g.: <i>K8s - exposed svcs and ingresses</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[r1:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[r2:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    OPTIONAL MATCH(i:K8sIngress)-[r3:TO_SERVICE]-(svc3:K8sService)
    RETURN svc1,r1,ip,svc2,r2,dom,i,r3,svc3</pre>
  </details>

### K8s - pods exposed via svcs and ingresses
`Show all the services with an external IP or domain and all the ingresses`
  <details>
  <summary>e.g.: <i>K8s - pods exposed via svcs and ingresses</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[r1:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[r2:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    OPTIONAL MATCH(i:K8sIngress)-[r3:TO_SERVICE]-(svc3:K8sService)
    WITH *,collect(svc1)+collect(svc2)+collect(svc3) as svcs
    UNWIND svcs as svc
    MATCH(p:K8sPod)-[r4:HAS_SERVICE]->(svc:K8sService)
    RETURN i,svc,p,r1,r2,r3,r4,ip,dom</pre>
  </details>

### K8s - privileged sas running in exposed pods
`Show all the service accounts with privilege escalation possibilities running in a pod accesible externally`
  <details>
  <summary>e.g.: <i>KK8s - sas running in exposed pods</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    OPTIONAL MATCH(i:K8sIngress)-[:TO_SERVICE]-(svc3:K8sService)
    WITH *,collect(svc1)+collect(svc2)+collect(svc3) as svcs
    UNWIND svcs as svc
    MATCH (svc)<-[:HAS_SERVICE]-(p:K8sPod)-[r:RUN_IN]-(sa:K8sServiceAccount)-[:PRIVESC]->(u)
    RETURN p,r,sa,svc,i</pre>
  </details>
</details>
</details>