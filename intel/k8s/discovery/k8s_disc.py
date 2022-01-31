import logging
import json
from intel.k8s.models import K8sPod, K8sContainer, K8sVol, K8sEnvVar, K8sSecret, K8sNamespace, K8sNode, K8sServiceAccount, K8sPodTemplate, K8sContainerPort
from intel.k8s.discovery.k8s_disc_client import K8sDiscClient
from kubernetes import client

class K8sDisc(K8sDiscClient):
    logger = logging.getLogger(__name__)

    def __init__(self, cred, **kwargs) -> None:
        super().__init__(get_creds=False)
        self.cred: client.__class__ = cred
        self.k8s_get_secret_values = kwargs.get("k8s_get_secret_values", False)
        self.task_name = "K8s"
    

    def _pod_selector(self, orig: K8sPodTemplate, dict_of_labels):
        """Given an origin and a dictionary of labels, find the related pods"""

        # Get resources using the service
        if dict_of_labels:
            search_str = " AND ".join([ f'((_.labels =~ ".*{k}.*" AND _.labels =~ ".*{v}.*") OR _.name = "{v}")' for k,v in dict_of_labels.items()])
            ress = K8sPod.get_all_by_kwargs(search_str)
            if not ress:
                self.logger.warning(f"No resources found using service {orig.name} with search {search_str}")

            else:
                for k8s_obj in ress:
                    orig.pods.update(k8s_obj)
                orig.save()


    def _save_container(self, pod_obj: K8sPod, container, ns_name: str):
        """
        Save the container and relate it with the pod it's running in.
        Get also the volumes and env vars
        """

        sc = container.security_context
        
        container_obj = K8sContainer(
            command = container.command,
            args = container.args,
            working_dir = container.working_dir,
            image_pull_policy = container.image_pull_policy,
            lifecycle_post_start = json.dumps(container.lifecycle.post_start) if container.lifecycle else "",
            lifecycle_pre_stop = json.dumps(container.lifecycle.post_start) if container.lifecycle else "",
            name = container.name,
            exist_limit_resources = bool(container.resources.limits),
            
            sc_allowPrivilegeEscalation = not sc.allow_privilege_escalation is False if hasattr(sc, "allow_privilege_escalation") else True,
            sc_capabilities_drop = sc.capabilities.drop if hasattr(sc, "capabilities") and hasattr(sc.capabilities, "drop") else [],
            sc_capabilities_add = sc.capabilities.add if hasattr(sc, "capabilities") and hasattr(sc.capabilities, "add") else [],
            sc_privileged = sc.privileged if hasattr(sc, "privileged") else False,
            sc_procMount = sc.proc_mount if hasattr(sc, "proc_mount") else "",
            sc_readOnlyRootFilesystem = sc.read_only_root_filesystem if hasattr(sc, "read_only_root_filesystem") else False,
            sc_runAsGroup = sc.run_as_group if hasattr(sc, "run_as_group") else "",
            sc_runAsNonRoot = sc.run_as_non_root if hasattr(sc, "run_as_non_root") else False,
            sc_runAsUser = sc.run_as_user if hasattr(sc, "run_as_user") else "",
            sc_seLinuxOptions = json.dumps(sc.se_linux_options) if hasattr(sc, "se_linux_options") else None,
            sc_seccompProfile = json.dumps(sc.seccomp_profile) if hasattr(sc, "seccomp_profile") else None,
            sc_windowsOptions = json.dumps(sc.windows_options) if hasattr(sc, "windows_options") else None,
        ).save()

        if container.ports:
            for p in container.ports:
                container_port_obj = K8sContainerPort(
                    name = p.name,
                    port = p.container_port,
                    protocol = p.protocol,
                ).save()
                container_obj.container_ports.update(container_port_obj, host_port=p.host_port, host_ip=p.host_ip)

        if container.volume_mounts:
            for volume in container.volume_mounts:
                vol_obj = K8sVol(
                    name = f"{ns_name}:{volume.name}",
                ).save()
                container_obj.volumes.update(vol_obj, mount_path = volume.mount_path,
                                                        mount_propagation = volume.mount_propagation,
                                                        read_only = volume.read_only,
                                                        sub_path = volume.sub_path,
                                                        sub_path_expr = volume.sub_path_expr
                                            )

        if container.env:
            for env in container.env:
                envvar_obj = K8sEnvVar(
                    name = f"{ns_name}:{env.name}",
                ).save()
                if hasattr(env, "value"):
                    container_obj.envvars.update(envvar_obj, value=env.value)
                
                elif hasattr(env, "valueFrom"):
                    container_obj.envvars.update(envvar_obj, value=f"secret:{env.valueFrom.secretKeyRef.name}.{env.valueFrom.secretKeyRef.key}")
                    secret_obj = K8sSecret(
                        name = f"{ns_name}:{env.valueFrom.secretKeyRef.name}",
                    ).save()
                    secret_obj.envvars.update(envvar_obj)
                    container_obj.secrets.update(secret_obj, key=env.valueFrom.secretKeyRef.key)
                
                else:
                    self.logger.error(f"Unknown type of env var value {env}")

        container_obj.save()
        pod_obj.containers.update(container_obj)


    def _save_pod(self, pod, orig: K8sPodTemplate, ns_name, **kwargs):
        """Give K8s pod details, save it"""
        
        if type(orig) is K8sNamespace:
            ns_obj = orig
            ns_name = ns_obj.name
        else:
            ns_name = ns_name
            ns_obj = K8sNamespace(name = ns_name).save()
        
        sc = pod.spec.security_context
        pod_name = f"{ns_name}:{pod.metadata.name}" if pod.metadata.name else f"{orig.name}-pod-template" #orig.name already has the namespace name
        pod_obj = K8sPod(
            name = pod_name,
            generate_name = pod.metadata.generate_name,
            self_link = pod.metadata.self_link,
            uid = pod.metadata.uid,
            labels = json.dumps(pod.metadata.labels),
            iam_amazonaws_com_role = pod.metadata.annotations.get("iam.amazonaws.com/role", "") if pod.metadata.annotations else "",
            iam_amazonaws_external_id = pod.metadata.annotations.get("iam.amazonaws.com/external-id", "") if pod.metadata.annotations else "",
            annotations = json.dumps(pod.metadata.annotations) if pod.metadata.annotations else "",

            dnsPolicy = pod.spec.dns_policy,
            enableServiceLinks = pod.spec.enable_service_links,
            imagePullSecrets = [ips.name for ips in pod.spec.image_pull_secrets] if pod.spec.image_pull_secrets else [],
            priority = pod.spec.priority,
            priorityClassName = pod.spec.priority_class_name,
            restartPolicy = pod.spec.restart_policy,
            schedulerName = pod.spec.scheduler_name,
            no_automount_service_account_token = not bool(pod.spec.automount_service_account_token),

            host_ipc = bool(pod.spec.host_ipc),
            host_network = bool(pod.spec.host_network),
            host_pid = bool(pod.spec.host_pid),
            host_path = [],

            sc_fsGroup = sc.fs_group if hasattr(sc, "fs_group") else "",
            sc_fsGroupChangePolicy = sc.fs_group if hasattr(sc, "fs_group_change_policy") else "",
            sc_runAsGroup = sc.run_as_group if hasattr(sc, "run_as_group") else "",
            sc_runAsNonRoot = sc.run_as_non_root if hasattr(sc, "run_as_non_root") else False,
            sc_runAsUser = sc.run_as_user if hasattr(sc, "run_as_user") else "",
            sc_seLinuxOptions = json.dumps(sc.se_linux_options) if hasattr(sc, "se_linux_options") else "",
            sc_seccompProfile = json.dumps(sc.seccomp_profile) if hasattr(sc, "seccomp_profile") else "",
            sc_supplemental_groups = sc.supplemental_groups if hasattr(sc, "sc_supplemental_groups") else [],
            sc_sysctls = sc.sysctls if hasattr(sc, "sc_sysctls") else [],
            sc_windowsOptions = json.dumps(sc.windows_options) if hasattr(sc, "windows_options") else "",

            phase = pod.status.phase if hasattr(pod, "status") else "",
            pod_ips = [ip.ip for ip in pod.status.pod_i_ps] if hasattr(pod, "status") and pod.status.pod_i_ps else []
        ).save()
        pod_obj.namespaces.update(ns_obj)

        # Save volumes and volumes secrets
        if pod.spec.volumes:
            for volume in pod.spec.volumes:
                vol_obj = K8sVol(
                    name = f"{ns_name}:{volume.name}",
                    is_hostpath = bool(volume.host_path)
                ).save()
                pod_obj.volumes.update(vol_obj)

                if volume.host_path:
                    pod_obj.host_path.append(volume.host_path.path)

                if volume.secret:
                    secret_obj = K8sSecret(
                        name = f"{ns_name}:{volume.secret.secret_name}"
                    ).save()
                    secret_obj.namespaces.update(ns_obj)
                    secret_obj.volumes.update(vol_obj)
                    secret_obj.save()

                    pod_obj.secrets.update(secret_obj, defaultMode=volume.secret.default_mode)

        node_name = pod.spec.node_name
        if node_name:
            node_obj = K8sNode(name = node_name).save()
            pod_obj.nodes.update(node_obj)

        sa_name = pod.spec.service_account_name if pod.spec.service_account_name else pod.spec.service_account
        if sa_name:
            sa_obj = K8sServiceAccount(name = f"{ns_name}:{sa_name}", potential_escape_to_node=False).save()
            sa_obj.namespaces.update(ns_obj)
            sa_obj.save()
            pod_obj.serviceaccounts.update(sa_obj)

        if pod.spec.init_containers or pod.spec.containers:
            if pod.spec.init_containers:
                for container in pod.spec.init_containers:
                    self._save_container(pod_obj, container, ns_name)
            
            else:
                for container in pod.spec.containers:
                    self._save_container(pod_obj, container, ns_name)

        pod_obj.save()
        orig.pods.update(pod_obj)
        orig.save()
