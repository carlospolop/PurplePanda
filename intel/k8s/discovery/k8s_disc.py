import logging
import json
from time import sleep
from intel.k8s.models import K8sPod, K8sContainer, K8sVol, K8sEnvVar, K8sSecret, K8sNamespace, K8sNode, K8sServiceAccount, K8sPodTemplate, K8sContainerPort, K8sBasicModel
from intel.k8s.discovery.k8s_disc_client import K8sDiscClient
from core.models.models import ContainerImage
from kubernetes import client

class K8sDisc(K8sDiscClient):
    logger = logging.getLogger(__name__)

    def __init__(self, cred, config, cluster_id, **kwargs) -> None:
        super().__init__(get_creds=False)
        self.cred: client.__class__ = cred
        self.config = config
        self.k8s_get_secret_values = kwargs.get("k8s_get_secret_values", False)
        self.task_name = "K8s"
        self.cluster_id = str(cluster_id)
        self.belongs_to = kwargs.get("belongs_to")
    
    def rel_to_cloud_cluster(self, k8s_obj):
        """Try to realte the cluster object to the cloud clouster it belongs to"""
        
        if self.belongs_to:
            k8s_obj.cloudclusters.update(self.belongs_to)
            k8s_obj.save()
    
    def call_k8s_api(self, f, **kwargs):
        """Handle the error when calling K8s APIs"""

        # Get counter and remove it from the kwargs to not cause problems
        cont = 0
        if kwargs.get("cont"):
            cont = kwargs["cont"]
            del kwargs["cont"]
        
        try:
            return f(**kwargs)
        
        except client.exceptions.ApiException as e:
            if e.status == 401 and cont < 2:
                self.logger.warning("401 in K8s request, sleeping 20s an retrying")
                sleep(20)
                if not self.reload_api(): 
                    return None
                
                else:
                    f.__self__.api_client = self.cred #Update to new client
                    cont += 1
                    kwargs["cont"] = cont
                    return self.call_k8s_api(f, **kwargs)

            elif e.status == 401:
                self.logger.warning("The solution didn't work")
                return None

        except:
            return None
    
    def reload_api(self):
        cred = self._get_cred(self.config)
        if not cred:
            self.logger.error("I couldn't reload the kubernetes key")
            return False
        
        self.cred = cred["cred"]
        return True


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


    def _save_ns_by_name(self, ns_name:str):
        """Given the name of the NS, save it"""

        name = f"{self.cluster_id}-{ns_name}" if not ns_name.startswith(str(self.cluster_id)) else ns_name
        ns_obj = K8sNamespace(name=name, ns_name=ns_name).save()
        self.rel_to_cloud_cluster(ns_obj)
        return ns_obj.save()


    def _save_container(self, pod_obj: K8sPod, container, ns_name: str):
        """
        Save the container and relate it with the pod it's running in.
        Get also the volumes and env vars
        """

        sc = container.security_context

        post_start = container.lifecycle.post_start if container.lifecycle else {}
        lifecycle_post_start = {
            "exec": post_start._exec.command if post_start._exec else "",
            "tcpSocket": f"{post_start.tcp_socket.host}:{post_start.tcp_socket.port}" if post_start.tcp_socket else "",
            "httpGet": f"{post_start.http_get.scheme}://{post_start.http_get.host}:{post_start.http_get.port}/{post_start.http_get.path}" if post_start.http_get else "",
        } if post_start else {}

        pre_stop = container.lifecycle.pre_stop if container.lifecycle else {}
        lifecycle_pre_stop = {
            "exec": pre_stop._exec.command if pre_stop._exec else "",
            "tcpSocket": f"{pre_stop.tcp_socket.host}:{pre_stop.tcp_socket.port}" if pre_stop.tcp_socket else "",
            "httpGet": f"{pre_stop.http_get.scheme}://{pre_stop.http_get.host}:{pre_stop.http_get.port}/{pre_stop.http_get.path}" if pre_stop.http_get else "",
        } if pre_stop else {}
        
        container_obj = K8sContainer(
            command = container.command,
            args = container.args,
            working_dir = container.working_dir,
            image = container.image,
            image_pull_policy = container.image_pull_policy,
            lifecycle_post_start = json.dumps(lifecycle_post_start) if lifecycle_post_start else "",
            lifecycle_pre_stop = json.dumps(lifecycle_pre_stop) if lifecycle_pre_stop else "",
            name = container.name,
            exist_limit_resources = bool(container.resources.limits),
            limits = str(container.resources.limits),
            
            sc_allowPrivilegeEscalation = not sc.allow_privilege_escalation is False if hasattr(sc, "allow_privilege_escalation") else True,
            sc_capabilities_drop = sc.capabilities.drop if hasattr(sc, "capabilities") and hasattr(sc.capabilities, "drop") else [],
            sc_capabilities_add = sc.capabilities.add if hasattr(sc, "capabilities") and hasattr(sc.capabilities, "add") else [],
            sc_privileged = sc.privileged if hasattr(sc, "privileged") else False,
            sc_procMount = sc.proc_mount if hasattr(sc, "proc_mount") else "",
            sc_readOnlyRootFilesystem = sc.read_only_root_filesystem if hasattr(sc, "read_only_root_filesystem") else False,
            sc_runAsGroup = sc.run_as_group if hasattr(sc, "run_as_group") else "",
            sc_runAsNonRoot = sc.run_as_non_root if hasattr(sc, "run_as_non_root") else False,
            sc_runAsUser = sc.run_as_user if hasattr(sc, "run_as_user") else "",
            sc_seLinuxOptions = str(sc.se_linux_options) if hasattr(sc, "se_linux_options") else None,
            sc_seccompProfile = f"{sc.seccomp_profile.localhost_profile}-{sc.seccomp_profile.type}" if hasattr(sc, "seccomp_profile") and hasattr(sc.seccomp_profile, "seccomp_profile") and sc.seccomp_profile.localhost_profile else None,
            sc_windowsOptions = str(sc.windows_options) if hasattr(sc, "windows_options") else None,
            sc_windowsOptions_local_vars = str(sc.windows_options.local_vars_configuration.__dict__) if hasattr(sc, "windows_options") and hasattr(sc.windows_options, "local_vars_configuration") else None,
        ).save()

        if container.image:
            conimg_obj = ContainerImage(name=container.image).save()
            container_obj.run_images.update(conimg_obj)
            container_obj.save()

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


    def _save_pod(self, pod, **kwargs):
        """Give K8s pod details, save it"""
        
        orig: K8sPodTemplate = kwargs["orig"]
        ns_name = kwargs["ns_name"]

        if type(orig) is K8sNamespace:
            ns_obj = orig
        else:
            ns_obj = self._save_ns_by_name(ns_name)
        ns_name = ns_obj.name
        
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
            sc_seccompProfile_type = sc.seccomp_profile.type if hasattr(sc, "seccomp_profile") and sc.seccomp_profile else "",
            sc_seccompProfile_localhost_profile = sc.seccomp_profile.localhost_profile if hasattr(sc, "seccomp_profile") and sc.seccomp_profile else "",
            sc_supplemental_groups = sc.supplemental_groups if hasattr(sc, "sc_supplemental_groups") else [],
            sc_sysctls = sc.sysctls if hasattr(sc, "sc_sysctls") else [],
            sc_windowsOptions = json.dumps(sc.windows_options) if hasattr(sc, "windows_options") else "",

            phase = pod.status.phase if hasattr(pod, "status") else "",
            pod_ips = [ip.ip for ip in pod.status.pod_i_ps] if hasattr(pod, "status") and pod.status.pod_i_ps else []
        ).save()
        pod_obj.namespaces.update(ns_obj)

        # If namespaces, origin already saved
        if type(orig) is not K8sNamespace:
            orig.pods.update(pod_obj)
            orig.save()

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
