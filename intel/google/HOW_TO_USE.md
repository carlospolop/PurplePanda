# Investigation

## Privilege Escalation Queries

<details>
<summary>Details</summary>

### Gcp - privileged principals with limit $limit
`Show all the principals with privilege escalation possibilities with a limit to avoid eternal queries.`

<details>
    <summary>e.g.: <i>Gcp - Privileged Identities with limit 1000</i></summary>
    <pre>
    MATCH(ppal:Gcp)-[r:PRIVESC]->(res:Gcp)
    RETURN ppal, r, res LIMIT $limit</pre>
</details>

### Gcp - full privesc path from $ppal
`Get the full privilege escalation path of a principal.`

<details>
    <summary>e.g.: <i>Gcp - full privesc path from username@domain.com</i></summary>
    <pre>
    MATCH (ppal:GcpPrincipal) WHERE ppal.email = $ppal OR ppal.domain = $ppal OR ppal.name = $ppal
    WITH ppal
    OPTIONAL MATCH r1 =(ppal)-[:PRIVESC*..]->(res1)
    OPTIONAL MATCH r2 = (ppal)-[:MEMBER_OF*..]->(g)-[:PRIVESC*..]->(res2)
    WITH *, relationships(r1) as rels1, relationships(r2) as rels2
    RETURN ppal,res1,rels1,rels2,g,res2</pre>
</details>

### Gcp - full privesc path to organizations
`Get the full privilege escalation path to all organizations.`

<details>
    <summary>e.g.: <i>Gcp - full privesc path to organizations</i></summary>
    <pre>
    MATCH (res:GcpOrganization)
    MATCH (res)<-[r1:PRIVESC]-(ppal1)
    OPTIONAL MATCH r = (ppal1)<-[:MEMBER_OF*..]-(ppal2)
    WITH *, relationships(r) as rels
    RETURN res,r1,ppal1,ppal2,rels</pre>
</details>

### Gcp - full privesc path to $res
`Get the full privilege escalation path to a resource.`

<details>
    <summary>e.g.: <i>Gcp - full privesc path to organization/12323423423</i></summary>
    <pre>
    MATCH (res:GcpResource) WHERE res.email = $res OR ppal.domain = $res OR res.name = $res
    WITH res
    MATCH (res)<-[r1:PRIVESC]-(ppal1)
    OPTIONAL MATCH r = (ppal1)<-[:MEMBER_OF*..]-(ppal2)
    WITH *, relationships(r) as rels
    RETURN res,r1,ppal1,ppal2</pre>
</details>

### Gcp - privesc outside gcp
`Get the privescs from GCP principal to external platforms.`

<details>
    <summary>e.g.: <i>Gcp - privesc outside gcp</i></summary>
    <pre>
    MATCH(attacker:Gcp)-[r:PRIVESC]->(victim)
    WHERE not "Gcp" in labels(victim)
    RETURN attacker, r, victim</pre>
</details>
</details>

---

## Roles & Permissions
<details>
<summary>Details</summary>

### Gcp - permissions of role $role
`Show the permissions of a role.`

<details>
    <summary>e.g.: <i>Gcp - permissions of role roles/iam.securityAdmin</i></summary>
    <pre>
    MATCH(r:GcpRole{name: $role})-[c:CONTAINS]->(p:GcpPermission)
    RETURN r,c,p</pre>
</details>


### Gcp - roles of principal $ppal
`Show the roles of the principal over some resources.`

<details>
    <summary>e.g.: <i>Gcp - roles of principal email@domain.com</i></summary>
    <pre>
    MATCH (ppal:GcpPrincipal) WHERE ppal.email = $ppal OR identity.domain = $ppal OR identity.name = $ppal
    OPTIONAL MATCH (ppal)-[h1:HAS_ROLE]->(r1)
    OPTIONAL MATCH x = (ppal)-[:MEMBER_OF*..]->(pp)-[:HAS_ROLE]->(r2) 
    RETURN ppal,h1,r1,relationships(x),pp,r2</pre>
</details>


### Gcp - principals with role $role
`Show all the principals with a role.`
<details>
    <summary>e.g.: <i>Gcp - principals with role roles/iam.securityAdmin</i></summary>
    <pre>
    MATCH(p:GcpPrincipal)-[h:HAS_ROLE]->(r) WHERE $role in h.roles
    WITH p as principals, h as rol_rel, r as resources
    OPTIONAL MATCH x = (principals)<-[:MEMBER_OF*0..]-(members)
    WITH *, relationships(x) as rels
    RETURN principals,rol_rel,resources,members,rels</pre>
</details>


### Gcp - principals with permission $permission
`Show all the principals with a permission.`

<details>
    <summary>e.g.: <i>Gcp - Identities with permission iam.serviceAccounts.getAccessToken</i></summary>
    <pre>
    MATCH(r:GcpRole)-[c:CONTAINS]->(p:GcpPermission{name: $permission})
    WITH r.name as role_names
    OPTIONAL MATCH(p:GcpPrincipal)-[h:HAS_ROLE]->(r) WHERE any(x IN h.roles WHERE x IN role_names)
    WITH p as principals, h as rol_rel, r as resources
    OPTIONAL MATCH x = (p2)-[:MEMBER_OF*..]->(principals)
    WITH *, relationships(x) as rels
    RETURN principals,rol_rel,resources,p2,rels</pre>
</details>
</details>

---

## Principal Identities
<details>
<summary>Details</summary>

### Gcp - users and groups not from Workspace
`Show all the users and groups in the graph that aren't related to a workspace`

<details>
    <summary>e.g.: <i>Gcp - Get Users and Groups not from Workspace</i></summary>
    <pre>
    OPTIONAL MATCH (g:GoogleGroup) WHERE NOT EXISTS((g)-[:PART_OF]->(:GoogleWorkspace))
    OPTIONAL MATCH (u:GcpUserAccount) WHERE NOT EXISTS((u)-[:PART_OF]->(:GoogleWorkspace))
    RETURN g,u</pre>
</details>


### Gcp - Privileged groups
`Show all the groups with some privilege escalation path.`

<details>
    <summary>e.g.: <i>Gcp - Privileged groups</i></summary>
    <pre>
    MATCH (g:GoogleGroup)-[r:PRIVESC]->(b)
    RETURN g,r,b</pre>
</details>


### Gcp - roles of groups bigger than $number
`Show the roles of the groups bigger than the given number.`

<details>
    <summary>e.g.: <i>Gcp - roles of groups bigger than 250</i></summary>
    <pre>
    MATCH (grp:GoogleGroup)<-[:MEMBER_OF*0..]-(mem:GcpPrincipal)
    WITH grp, count(mem) as mem_count
    WHERE mem_count > $number
    OPTIONAL MATCH(grp)-[r:HAS_ROLE]-(res)
    RETURN grp, r, res</pre>
</details>

### Gcp - not just members of a group
`Show all the members of a group with extra privileges over it`

<details>
    <summary>e.g.: <i>Gcp - Not just members of a group</i></summary>
    <pre>
    MATCH ()-[r:MEMBER_OF]-() WHERE r.roles <> ["MEMBER"] 
    RETURN r.roles</pre>
</details>


### Gcp - users with direct roles $verbose
`Show all the users with direct roles over resources. Use $verbose > 1 to show also "roles/owner", "roles/editor" and "roles/viewer" roles.`

<details>
    <summary>e.g.: <i>Gcp - Users with direct roles 2</i></summary>
    <pre>
    MATCH (u:GcpUserAccount)-[rel:HAS_ROLE]->(res) 
    WHERE ($verbose <= 1 AND rel.roles <> ["roles/owner"] AND rel.roles <> ["roles/editor"] AND rel.roles <> ["roles/viewer"]) OR $verbose > 1
    RETURN u, rel, res</pre>
</details>


### Gcp - SAs with cross-project permissions
`Show all the SAs with a parent project that can access resources outside of their parent project.`

<details>
    <summary>e.g.: <i>Gcp - SAs with cross-project permissions</i></summary>
    <pre>
    MATCH (sa:GcpServiceAccount)-[rel:HAS_ROLE]->(res:Gcp) 
    WHERE EXISTS((sa)-[:PART_OF]->(:GcpProject)) AND NOT EXISTS((sa)-[:PART_OF]->(res)) AND NOT EXISTS((sa)-[:PART_OF]->(:GcpProject)<-[:PART_OF]-(res))
    RETURN sa, rel, res</pre>
</details>
</details>

---

## Privileges comparisons
<details>
<summary>Details</summary>

### Gcp - roles in $identity1 but not in $identity2 filtered by $filter
`Get roles that the first identity has and not the second filtered by a string.`

<details>
    <summary>e.g.: <i>Gcp - roles in user1@domain.com but not in user2@domain.com filtered by bigquery</i></summary>
    <pre>
    MATCH (identity2:GcpPrincipal) WHERE identity2.email = identity2.email = $identity2 OR identity2.domain = $identity2 OR identity2.name = $identity2
    OPTIONAL MATCH (identity2)-[h21:HAS_ROLE]->(r21)
    OPTIONAL MATCH (identity2)-[:MEMBER_OF*..]->()-[h22:HAS_ROLE]->(r22)
    OPTIONAL MATCH (role2:GcpRole)
    WITH role2, collect(h21) as h21_list, collect(h22) as h22_list
    WHERE toLower(role2.name) CONTAINS toLower($filter) AND (any(rel in h21_list WHERE role2.name IN rel.roles) OR any(rel in h22_list WHERE role2.name in rel.roles))
    WITH DISTINCT collect(role2.name) AS roles_identity_2
    MATCH (identity1:GcpPrincipal) WHERE identity1.email = $identity1 OR identity1.domain = $identity1 OR identity1.name = $identity1
    OPTIONAL MATCH (identity1)-[h11:HAS_ROLE]->(r11)
    OPTIONAL MATCH (identity1)-[:MEMBER_OF*..]->()-[h12:HAS_ROLE]->(r12)
    OPTIONAL MATCH (role1:GcpRole)
    WITH role1, collect(h11) as h11_list, collect(h12) as h12_list, roles_identity_2
    WHERE toLower(role1.name) CONTAINS toLower($filter) AND NOT role1.name IN roles_identity_2 AND (any(rel in h11_list WHERE role1.name IN rel.roles) OR any(rel in h12_list WHERE role1.name in rel.roles))
    RETURN role1</pre>
</details>

### Gcp - permissions in $identity1 but not in $identity2 filtered by $filter
`Get permissions that the first identity has and not the second and contains some string`

<details>
    <summary>e.g.: <i>Gcp - permissions in user1@domain.com but not in user2@domain.com filtered by bigquery</i></summary>
    <pre>
    MATCH (identity2:GcpPrincipal) WHERE identity2.email = identity2.email = $identity2 OR identity2.domain = $identity2 OR identity2.name = $identity2
    OPTIONAL MATCH (identity2)-[h21:HAS_ROLE]->(r21)
    OPTIONAL MATCH (identity2)-[:MEMBER_OF*..]->()-[h22:HAS_ROLE]->(r22)
    OPTIONAL MATCH (perm2:GcpPermission)<-[:CONTAINS]-(role2:GcpRole)
    WITH perm2, role2, collect(h21) as h21_list, collect(h22) as h22_list
    WHERE toLower(perm2.name) CONTAINS toLower($filter) AND any(rel in h21_list WHERE role2.name IN rel.roles) OR any(rel in h22_list WHERE role2.name in rel.roles)
    WITH DISTINCT collect(perm2.name) AS perms_names_2
    MATCH (identity1:GcpPrincipal) WHERE identity1.email = $identity1 OR identity1.domain = $identity1 OR identity1.name = $identity1
    OPTIONAL MATCH (identity1)-[h11:HAS_ROLE]->(r11)
    OPTIONAL MATCH (identity1)-[:MEMBER_OF*..]->()-[h12:HAS_ROLE]->(r12)
    OPTIONAL MATCH (perm1:GcpPermission)<-[:CONTAINS]-(role1:GcpRole)
    WITH perm1, role1, collect(h11) as h11_list, collect(h12) as h12_list, perms_names_2
    WHERE toLower(perm1.name) CONTAINS toLower($filter) AND NOT perm1.name IN perms_names_2 AND (any(rel in h11_list WHERE role1.name IN rel.roles) OR any(rel in h12_list WHERE role1.name in rel.roles))
    RETURN perm1</pre>
</details>
</details>

---

## MISC

<details>
<summary>Details</summary>

### Gcp - Open Resources
`Show all the resources open to all users`

<details>
    <summary>e.g.: <i>Gcp - Open Resources</i></summary>
    <pre>
    MATCH(u:GcpUserAccount)-[role:HAS_ROLE]->(resource) WHERE u.name="allUsers" OR u.name="allAuthenticatedUsers"
    RETURN u,role,resource</pre>
</details>

### Gcp - open FW rules and public VMs $verbose
`Show all the firewall rules open to the internet and all the machines with public IPs. Use verbose > 1 for a more specific search.`

<details>
    <summary>e.g.: <i>Gcp - open FW rules and public VMs 2</i></summary>
    <pre>
    OPTIONAL MATCH (fw:GcpFirewallRule)-[fw_r:PROTECT]-(fw_n:GcpNetwork)
    WHERE fw.direction = "INGRESS" AND
    ( 
        ($verbose > 2 OR fw.allowed <> ["icmp:*"])
        AND
        (
            any(iprange in fw.sourceRanges WHERE iprange CONTAINS "0.0.0.0" OR iprange CONTAINS "::/0")
            OR
            ($verbose > 1 AND (
                any(iprange in fw.sourceRanges WHERE 
                    NOT any(priv_reg in ["^127\..*","^10\..*", "^172\.1[6-9]\..*", "^172\.2[0-9]\..*", "^172\.3[0-1]\..*", "^192\.168\..*"] WHERE iprange =~ priv_reg)
                ) 
            ))
        )
    )
    OPTIONAL MATCH (c:GcpComputeInstance)-[c_r:CONNECTED]-(sn:GcpSubnetwork)-[pn:PART_OF]-(n:GcpNetwork) WHERE 
    any(ip_addr IN c_r.accessConfigs_natIPs WHERE NOT 		any(priv_reg in ["^127\..*","^10\..*", "^172\.1[6-9]\..*", "^172\.2[0-9]\..*", "^172\.3[0-1]\..*", "^192\.168\..*"] WHERE ip_addr =~ priv_reg)
    )
    OPTIONAL MATCH (composer:GcpComposerEnv)<-[p_o:PART_OF]-(cluster:GcpCluster) WHERE 
    any(iprange IN composer.allowedIpRanges WHERE NOT 		any(priv_reg in ["^127\..*","^10\..*", "^172\.1[6-9]\..*", "^172\.2[0-9]\..*", "^172\.3[0-1]\..*", "^192\.168\..*"] WHERE iprange =~ priv_reg)
    )
    RETURN fw, fw_r, fw_n, c, c_r, sn, pn, n, composer, p_o, cluster</pre>
</details>

### Gcp - SA with API keys
`Show all the SAs with API keys generated.`

<details>
    <summary>e.g.: <i>Gcp - SA with API keys</i></summary>
    <pre>
    MATCH(sa:GcpServiceAccount)-[r:HAS_KEY]->(k)
    RETURN sa,r,k</pre>
</details>

### Gcp - projects with permissions over others resources

<details>
    <summary>e.g.: <i>Gcp - Projects with permissions over others resources</i></summary>
    <pre>
    MATCH (p:GcpProject)-[hbr:HAS_BASIC_ROLES]->(r) WHERE NOT EXISTS((r)-[:PART_OF]->(p))
    RETURN p,hbr,r</pre>
</details>

### Gcp - unused assets
`Show elements in Gcp that aren't used`

<details>
    <summary>e.g.: <i>Gcp - unused assets</i></summary>
    <pre>
    OPTIONAL MATCH (isolated:Gcp) WHERE NOT EXISTS((isolated)-[]-())
    OPTIONAL MATCH (disabled:Gcp) WHERE disabled.disabled = True OR disabled.enabled = False
    OPTIONAL MATCH (orgs:GcpOrganization) WHERE NOT EXISTS((orgs)<-[:PART_OF]-())
    OPTIONAL MATCH (folders:GcpFolder) WHERE NOT EXISTS((folders)<-[:PART_OF]-())
    OPTIONAL MATCH (projects:GcpProject) WHERE NOT EXISTS((projects)<-[:PART_OF]-())
    OPTIONAL MATCH (groups:GoogleGroup) WHERE NOT EXISTS((groups)<-[:MEMBER_OF]-())
    OPTIONAL MATCH (sn:GcpSubnetwork) WHERE NOT EXISTS((sn)<-[:CONNECTED]-())
    OPTIONAL MATCH (user:GcpUserAccount) WHERE NOT EXISTS((user)-[:MEMBER_OF]->()) AND NOT EXISTS((user)-[:HAS_ROLE]->())
    RETURN isolated, disabled, orgs, folders, projects, groups, sn, user</pre>
</details>

### Gcp - Cluster creds
`Show all the clusters with username, password or clientkey.`

<details>
    <summary>e.g.: <i>Gcp - Cluster creds</i></summary>
    <pre>
    MATCH (cluster:GcpCluster)
    WHERE cluster.master_username <> "" OR cluster.master_password <> "" OR cluster.clientKey <> ""
    RETURN cluster</pre>
</details>

### Gcp - Custom Roles
`Show all the custom roles.`

<details>
    <summary>e.g.: <i>Gcp - Get Custom Roles</i></summary>
    <pre>
    MATCH (role:GcpRole)-[r:PART_OF]->(b)
    RETURN role,r,b</pre>
</details>

### Gcp - non-existent roles
`Show all the roles that are granted but wasn't found.`

<details>
    <summary>e.g.: <i>Gcp - Get non-existent roles</i></summary>
    <pre>
    MATCH(g:GcpPrincipal)-[r:HAS_ROLE]-(b) WHERE any(role_name in r.roles WHERE NOT exists( (:GcpRole{name: role_name})-[]-() ) ) 
    RETURN g,r,b</pre>
</details>

### Gcp - secret values
`Show all the gathered secret values.`

<details>
    <summary>e.g.: <i>Gcp - secret values</i></summary>
    <pre>
    MATCH (secret_version:GcpSecretVersion)
    WHERE secret_version.value <> ""
    RETURN secret_version</pre>
</details>
</details>
