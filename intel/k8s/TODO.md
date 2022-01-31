- When looking for privileges escalations where are only considering root level resources like "pods" or "replicasets". However, resources must be something like "pods/log" (resource/subresource). At the moment we are just using the first level, which can end in false possitives. We should update the `privesc.yaml` file in `k8s/info/privesc.yaml` indicating the minimun subresources needed to escalate privileges with each technique and then modify the code inside `analyze_results.py` to take into account subresources.

- At the moment we are just keeping the last binding between a principal and a resource, we should keep all of them (potentially merging them so the next TODO is also solved). CHeck around line 157 in `disc_roles.py`.

- At the moment all the techniques to escalate privileges require 1 verb. In the future they may require more than one. Now we are just checking if all the resources and verbs of a privesc technique are satified within 1 binding, but if more than 1 verb is needed it might be satisfied in 2 different bindings, therefore the process to check if a principal has access over a resource should consider all the bindings over the resource and not just 1 by 1.

- The relation between ingresses and services in disc_ingresses should be able to be more than 1
