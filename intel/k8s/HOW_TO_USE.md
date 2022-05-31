# Investigation

In this section we are going to explain how to use PurplePanda to **find potential problems within your kubernetes cluster** and possible **privilege escalation paths from K8s to other clouds**.

## Red, Purple & Blue Teams

Searching for **sensitive information in secrets and environment variables** is something all the teams should do. And the same happens when looking for **publicly exposed** endpoints.

### Secrets

*Note that it's possible that not all the secrets values were retrived if you didn't have enough permissions.*

<details>
<summary><b>Show queries to search secrets</b></summary>

#### K8s - secrets with values
`Show all the secrets with values discovered`
  <details>
  <summary>e.g.: <i>K8s - secrets with values</i></summary>
    <pre>
    MATCH(s:K8sSecret)
    WHERE s.values <> []
    RETURN s</pre>
  </details>

#### K8s - secrets with name filtered by $filter
`Show all the secrets whose name contains $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - secrets filtered by token</i></summary>
    <pre>
    MATCH(s:K8sSecret)
    WHERE toLower(s.name) CONTAINS toLower($filter) 
    RETURN s</pre>
  </details>

#### K8s - secrets with value filtered by $filter
`Show all the secrets whose name contains $filter (case insensitive search)`
  <details>
  <summary>e.g.: <i>K8s - secrets with value filtered by AI</i></summary>
    <pre>
    MATCH(s:K8sSecret)
    WHERE  any(text in s.values_cleartext WHERE text CONTAINS $filter) 
    RETURN s</pre>
  </details>
</details>

### Environment variables

<details>
<summary><b>Show queries to search environment variables</b></summary>

#### K8s - envars with value
`Show all the environment variables with a value not being a secret`
  <details>
  <summary>e.g.: <i>K8s - envars with value</i></summary>
    <pre>
    MATCH(e:K8sEnvVar)<-[r:USE_ENV_VAR]-(c:K8sContainer)
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

### Exposed services and Ingresses

<details>
<summary><b>Show queries to search exposed endpoints</b></summary>

#### K8s - pods exposed via svcs and ingresses
`Show all the services with an external IP or domain and all the ingresses`
  <details>
  <summary>e.g.: <i>K8s - pods exposed via svcs and ingresses</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[r1:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[r2:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    OPTIONAL MATCH(i:K8sIngress)-[r3:TO_SERVICE]-(svc3:K8sService)
    WITH *,collect(svc1)+collect(svc2)+collect(svc3) as svcs
    UNWIND svcs as svc
    OPTIONAL MATCH(p:K8sPod)-[r4:HAS_SERVICE]-(svc:K8sService)
    RETURN i,svc,p,r1,r2,r3,r4,ip,dom</pre>
  </details>

#### K8s - privileged exposed pods
`Show all the privileged pods accesible externally`
  <details>
  <summary>e.g.: <i>K8s - privileged exposed pods</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    OPTIONAL MATCH(i:K8sIngress)-[r1:TO_SERVICE]-(svc3:K8sService)
    WITH *,collect(svc1)+collect(svc2)+collect(svc3) as svcs
    UNWIND svcs as svc
    MATCH (svc)<-[r2:HAS_SERVICE]-(p:K8sPod)
    WHERE p.sc_runAsUser = 0 OR 
      p.sc_runAsNonRoot <> True AND p.sc_runAsUser = "" OR
      p.sc_runAsGroup < 50 OR
      any(grp in p.sc_supplemental_groups WHERE grp < 50) OR
      p.host_network OR
      p.host_pid OR
      p.host_ipc OR
      any(path IN p.host_path WHERE any( regex IN ["/", "/proc.*", "/sys.*", "/dev.*", "/var", "/var/", "/var/log.*", "/var/run.*", ".*docker.sock", ".*crio.sock", ".*/kubelet.*", ".*/pki.*", "/home/admin.*", "/etc.*", ".*/kubernetes.*", ".*/manifests.*", "/root.*"] WHERE regex =~ replace(path,"\\", "\\\\")))
    RETURN i,r1,svc,r2,p</pre>
  </details>

#### K8s - sas running in exposed pods
`Show all the service accounts running in a pod accesible externally`
  <details>
  <summary>e.g.: <i>K8s - sas running in exposed pods</i></summary>
    <pre>
    OPTIONAL MATCH(svc1:K8sService)-[:HAS_IP]-(ip:PublicIP)
    OPTIONAL MATCH(svc2:K8sService)-[:HAS_DOMAIN]-(dom:PublicDomain) WHERE dom.is_external = True
    OPTIONAL MATCH(i:K8sIngress)-[:TO_SERVICE]-(svc3:K8sService)
    WITH *,collect(svc1)+collect(svc2)+collect(svc3) as svcs
    UNWIND svcs as svc
    OPTIONAL MATCH (svc)<-[:HAS_SERVICE]-(p:K8sPod)-[r:RUN_IN]-(sa:K8sServiceAccount)
    RETURN p,r,sa</pre>
  </details>
</details>

### Privesc and permissions
<details>
<summary><b>Show queries to search unexpected privescs</b></summary>

#### K8s - authenticated ppals with privesc
`Show default SAs that can escalate privileges`
  <details>
  <summary>e.g.: <i>K8s - authenticated ppals with privesc</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal)-[r:PRIVESC]->(u)
    WHERE ppal.name CONTAINS "system:authenticated"
    RETURN ppal,r,u</pre>
  </details>

#### K8s - unauthenticated ppals with privesc
`Show default SAs that can escalate privileges`
  <details>
  <summary>e.g.: <i>K8s - unauthenticated ppals with privesc</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal)-[r:PRIVESC]->(u) WHERE ppal.name CONTAINS "system:unauthenticated" OR ppal.name CONTAINS "system:anonymous"
    RETURN ppal,r,u</pre>
  </details>

#### K8s - authenticated permissions
`Show permissions of every authenticated principal`
  <details>
  <summary>e.g.: <i>K8s - authenticated permissions</i></summary>
    <pre>
    MATCH (g:K8sGroup)-[perms:HAS_PERMS]->(victim)
    WHERE g.name CONTAINS "system:authenticated"
    RETURN g,perms,victim</pre>
  </details>

#### K8s - unauthenticated permissions
`Show permissions of unauthenticated principals`
  <details>
  <summary>e.g.: <i>K8s - authenticated permissions</i></summary>
    <pre>
    MATCH (g:K8sGroup)-[perms:HAS_PERMS]->(victim) WHERE g.name CONTAINS "system:unauthenticated" OR g.name CONTAINS "system:anonymous"
    RETURN g,perms,victim</pre>
  </details>
</details>
</details>

---

## Purple & Blue Teams

In this in this section you can find the queries sugegsted to Purple and Blue teams who wants to **find vulnerable configurations across all the data without any specific starting point**.

### Potential Node Breakouts

The two most important ways to avoid someone from escaping is to:
- Make sure the attacker will never be root in the container
- Apply defensive mechanisms to not give the root user mechanisms to escape from the container

<details>
<summary><b>Show queries to search Pods & Containers misconfigured that could allow to privesc and escape to the node</b></summary>

#### K8s - priv pods
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
    any(path IN p.host_path WHERE any( regex IN ["/", "/proc.*", "/sys.*", "/dev.*", "/var/run.*", ".*docker.sock", ".*crio.sock", ".*/kubelet.*", ".*/pki.*", "/home/admin.*", "/etc.*", ".*/kubernetes.*", ".*/manifests.*", "/root.*"] WHERE regex =~ replace(path,"\\", "\\\\")))
    RETURN p</pre>
  </details>

#### K8s - priv containers
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
    p.sc_runAsUser = 0 OR 
    p.sc_runAsNonRoot <> True AND p.sc_runAsUser = "" OR
    p.sc_runAsGroup < 50 OR
    p.sc_allowPrivilegeEscalation = True
    RETURN p</pre>
  </details>
</details>

### Privilege Escalation

Certain permissions will allow **principals to escalate to other principals**. This will imply a privilege escalation.

Moreover, a privilege escalation can grant a principal **more privileges over other namespaces or even external clouds**.

<details>
<summary><b>Show queries to search privilege escalation vectors</b></summary>


#### K8s - ppals that can escape from a node
`Show all the principals that can escape from a container to the node`
  <details>
  <summary>e.g.: <i>K8s - ppals that can escape from a node</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal {potential_escape_to_node:True})
    RETURN ppal</pre>
  </details>


#### K8s - ppals with privesc
`Show all the principals that can escalate privileges`
  <details>
  <summary>e.g.: <i>K8s - ppals with privesc</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal)-[r:PRIVESC]->(u)
    RETURN ppal</pre>
  </details>


#### K8s - privesc in ns $ns
`Show the internal privilege escalation paths inside a namespace (depth 1 to avoid eternal queries)`
  <details>
  <summary>e.g.: <i>K8s - privesc in ns default</i></summary>
    <pre>
    MATCH (ns:K8sNamespace)<-[:PART_OF]-(ppal1:K8sPrincipal)-[r:PRIVESC]->(ppal2:K8sPrincipal)-[:PART_OF]->(ns)
    WHERE ns.name CONTAINS $ns
    RETURN ns,ppal1,r,ppal2</pre>
  </details>


#### K8s - sa external privesc to ns $ns
`Show the privilege escalation paths from principals to principals in different namespaces`
  <details>
  <summary>e.g.: <i>K8s - external privesc to ns default</i></summary>
    <pre>
    MATCH (ns:K8sNamespace)<-[r1:PART_OF]-(ppal1:K8sPrincipal)<-[r2:PRIVESC]-(ppal2:K8sServiceAccount)
    WHERE ns.name CONTAINS $ns AND NOT EXISTS( (ppal2)-[:PART_OF]->(ns) )
    RETURN ns,r1,ppal1,r2,ppal2</pre>
  </details>


#### K8s - full external privesc to ns $ns
`Show the full privilege escalation paths from principals to principals in different namespaces`
  <details>
  <summary>e.g.: <i>K8s - external privesc to ns default</i></summary>
    <pre>
    MATCH (ns:K8sNamespace)<-[:PART_OF]-(ppal1:K8sPrincipal)<-[r:PRIVESC]-(ppal2:K8sPrincipal)
    WHERE ns.name CONTAINS $ns AND NOT EXISTS( (ppal2)-[:PART_OF]->(ns) )
    RETURN ns,ppal1,r,ppal2</pre>
  </details>


#### K8s - sa from $ns1 privesc to ns $ns2
`Show the privilege escalation paths from principals to principals in different namespaces`
  <details>
  <summary>e.g.: <i>K8s - external privesc to ns default</i></summary>
    <pre>
    MATCH (ns1:K8sNamespace)<-[:PART_OF]-(ppal1:K8sPrincipal)-[r:PRIVESC]->(ppal2:K8sServiceAccount)-[:PART_OF]->(ns2:K8sNamespace)
    WHERE ns1.name CONTAINS $ns1 AND ns2.name CONTAINS $ns2
    RETURN ppal1,r,ppal2</pre>
  </details>


#### K8s - privesc to sa aws
`Show the privilege escalation path to service accounts with aws permissions (depth just 1 or it could never end)`
  <details>
  <summary>e.g.: <i>K8s - privesc to sa aws</i></summary>
    <pre>
    MATCH r = (sa:K8sServiceAccount)<-[:PRIVESC]-(ppal:K8sPrincipal) WHERE sa.iam_amazonaws_role_arn <> ""
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,sa</pre>
  </details>


#### K8s - privesc to pod aws
`Show the privilege escalation path to pods with aws permissions (depth just 1 or it could never end)`
  <details>
  <summary>e.g.: <i>K8s - privesc to pod aws</i></summary>
    <pre>
    MATCH (ns:K8sNamespace)<-[:PART_OF]-(p:K8sPod) WHERE p.iam_amazonaws_com_role <> ""
    MATCH (ns)<-[:PART_OF]-(ppal1:K8sPrincipal)<-[r:PRIVESC]-(ppal2:K8sPrincipal) WHERE r.title CONTAINS "pod creation"
    RETURN p,ppal2</pre>
  </details>


#### K8s - privesc to sa gcp
`Show the privilege escalation path to service accounts with gcp permissions (depth just 1 or it could never end)`
  <details>
  <summary>e.g.: <i>K8s - privesc to sa gcp</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal)-[r:PRIVESC]->(gcpsa:GcpServiceAccount)
    RETURN ppal,r,gcpsa</pre>
  </details>


#### K8s - default sas with privesc
`Show default SAs that can escalate privileges`
  <details>
  <summary>e.g.: <i>K8s - default sas with privesc</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal)-[r:PRIVESC]->(u)
    WHERE ppal.name =~ ".*:default"
    RETURN ppal,r,u</pre>
  </details>
</details>

---

## Red Teams

Usually Red Teams will **compromise a few set of credentials** and they will be interested in knowing how to **escalate privileges from there**. Therefore, the following queries are going to be similar to the ones of the Purple & Blue Teams sections but **having an account as starting point**.

<details>
<summary><b>Show queries to search privilege escalation vectors from a specific principal</b></summary>

#### K8s - node escape from $ppal with depth 2
`Show ways to escape to the node from a principal with a max depth of 2`
  <details>
  <summary>e.g.: <i>K8s - node escape from default:default with depth 2</i></summary>
    <pre>
    MATCH (ppal:K8sPrincipal) WHERE ppal.name CONTAINS $ppal
    OPTIONAL MATCH r = (ppal)-[:PRIVESC*..2]->(ppal2:K8sPrincipal) WHERE NOT ppal.potential_escape_to_node AND ppal2.potential_escape_to_node
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,ppal2</pre>
  </details>


#### K8s - privesc in ns $ns from $ppal with depth 2
`Show privilege escalation paths from a principal to a namespace indicating the depth of 2`
  <details>
  <summary>e.g.: <i>K8s - privesc in ns kube-system from default:default with depth 1</i></summary>
    <pre>
    MATCH r = (ppal:K8sPrincipal)-r:PRIVESC*..2]->(ppal2:K8sPrincipal)-[:PART_OF]->(ns:K8sNamespace)
    WHERE ppal.name CONTAINS $ppal AND ns.name CONTAINS $ns
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,ppal2</pre>
  </details>


#### K8s - privesc to sa aws from $ppal with depth 2
`Show the privilege escalation paths from a principals to service accounts with aws permissions with a 2 depth`
  <details>
  <summary>e.g.: <i>K8s - privesc to sa aws from default:default with depth 2</i></summary>
    <pre>
    MATCH r = (ppal:K8sPrincipal)-[:PRIVESC*..2]->(sa:K8sServiceAccount) WHERE sa.iam_amazonaws_role_arn <> "" AND ppal.name CONTAINS $ppal
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,sa</pre>
  </details>


#### K8s - privesc to pod aws from $ppal with depth 2
`Show the privilege escalation path from a principal to pods with aws permissions with a 2 depth`
  <details>
  <summary>e.g.: <i>K8s - privesc to pod aws from default:default with depth 2</i></summary>
    <pre>
    MATCH (p:K8sPod)-[:PART_OF]->(ns:K8sNamespace) WHERE p.iam_amazonaws_com_role <> ""
    MATCH (ns)<-[:PART_OF]-(ppal1:K8sPrincipal)<-[r:PRIVESC*0..2]-(ppal2:K8sPrincipal) WHERE r.title CONTAINS "pod creation" AND ppal2.name CONTAINS $ppal
    RETURN p,r,ppal1,ppal2</pre>
  </details>

#### K8s - privesc to sa gcp from $ppal with depth 2
`Show the privilege escalation path from a service account to service accounts with gcp permissions with a 2 depth`
  <details>
  <summary>e.g.: <i>K8s - privesc to sa gcp from default:default with depth 2</i></summary>
    <pre>
    MATCH r = (ppal:K8sPrincipal)-[:PRIVESC*..2]->(gcpsa:GcpServiceAccount)
    WHERE ppal2.name CONTAINS $ppal
    WITH *, relationships(r) as privescs
    RETURN ppal,privescs,gcpsa</pre>
  </details>
</details>
</details>