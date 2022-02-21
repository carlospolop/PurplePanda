from py2neo.ogm import Property, Label, RelatedTo, RelatedFrom

from intel.google.models.gcp_perm_models import GcpPrincipal, GcpResource
from intel.google.models.gcp_project import GcpProject
from intel.google.models.gcp_organization import GcpOrganization
from intel.google.models.google_group import GoogleGroup

class GcpServiceAccount(GcpPrincipal, GcpResource):
    __primarylabel__ = "GcpServiceAccount"
    __primarykey__ = "email"

    name = Property()
    email = Property()
    description = Property()
    displayName = Property()
    uniqueId = Property()
    default_sa = Property()

    groups = RelatedTo(GoogleGroup, "MEMBER_OF")
    projects = RelatedTo(GcpProject, "PART_OF")
    organizations = RelatedTo(GcpOrganization, "PART_OF")
    cloud_functions = RelatedTo("GcpCloudFunction", "RUN_IN")
    compute_instances = RelatedTo("GcpComputeInstance", "RUN_IN")
    api_keys = RelatedTo("GcpApiKey", "HAS_KEY")
    privesc_from_k8s = RelatedFrom("K8sPrincipal", "PRIVESC")

    gcp = Label(name="Gcp")

    def __init__(self, email, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_sa = any(ie in email for ie in internal_emails)        
        self.gcp = True



# From https://cloud.google.com/iam/docs/service-agents
internal_emails = [
    "-compute@developer.gserviceaccount.com",
    "gcp-sa-aiplatform-cc.iam.gserviceaccount.com",
    "gcp-sa-aiplatform.iam.gserviceaccount.com",
    "gcp-sa-meshcontrolplane.iam.gserviceaccount.com",
    "gcp-sa-meshdataplane.iam.gserviceaccount.com",
    "gcp-sa-accessapproval.iam.gserviceaccount.com",
    "gcp-sa-anthosaudit.iam.gserviceaccount.com",
    "gcp-sa-anthosconfigmanagement.iam.gserviceaccount.com",
    "gcp-sa-anthosidentityservice.iam.gserviceaccount.com",
    "gcp-sa-gkemulticloud.iam.gserviceaccount.com",
    "gcp-sa-anthos.iam.gserviceaccount.com",
    "gcp-sa-servicemesh.iam.gserviceaccount.com",
    "gcp-sa-anthossupport.iam.gserviceaccount.com",
    "gcp-sa-apigee.iam.gserviceaccount.com",
    "gcp-sa-appdevexperience.iam.gserviceaccount.com",
    "gae-api-prod.google.com.iam.gserviceaccount.com",
    "gcp-gae-service.iam.gserviceaccount.com",
    "gcp-sa-artifactregistry.iam.gserviceaccount.com",
    "gcp-sa-assuredworkloads.iam.gserviceaccount.com",
    "gcp-sa-recommendationengine.iam.gserviceaccount.com",
    "gcp-sa-automl.iam.gserviceaccount.com",
    "gcp-sa-gkebackup.iam.gserviceaccount.com",
    "bigquery-encryption.iam.gserviceaccount.com",
    "gcp-sa-bigqueryconnection.iam.gserviceaccount.com",
    "gcp-sa-bigquerydatatransfer.iam.gserviceaccount.com",
    "gcp-sa-prod-bigqueryomni.iam.gserviceaccount.com",
    "gcp-sa-binaryauthorization.iam.gserviceaccount.com",
    "gcp-sa-bundles.iam.gserviceaccount.com",
    "gcp-sa-notebooks.iam.gserviceaccount.com",
    "gcp-sa-apigateway-mgmt.iam.gserviceaccount.com",
    "gcp-sa-apigateway.iam.gserviceaccount.com",
    "gcp-sa-cloudasset.iam.gserviceaccount.com",
    "gcp-sa-bigtable.iam.gserviceaccount.com",
    "cloudbuild.gserviceaccount.com",
    "gcp-sa-cloudbuild.iam.gserviceaccount.com",
    "gcp-sa-certificatemanager.iam.gserviceaccount.com",
    "cloudcomposer-accounts.iam.gserviceaccount.com",
    "gcp-sa-datafusion.iam.gserviceaccount.com",
    "dlp-api.iam.gserviceaccount.com",
    "gcp-sa-datastream.iam.gserviceaccount.com",
    "gcp-sa-datamigration.iam.gserviceaccount.com",
    "dataflow-service-producer-prod.iam.gserviceaccount.com",
    "gcp-sa-dataplex.iam.gserviceaccount.com",
    "gcp-sa-clouddeploy.iam.gserviceaccount.com",
    "gcp-sa-endpoints.iam.gserviceaccount.com",
    "cloud-filer.iam.gserviceaccount.com",
    "gcp-sa-firestore.iam.gserviceaccount.com",
    "gcp-sa-healthcare.iam.gserviceaccount.com",
    "gcp-sa-cloud-ids.iam.gserviceaccount.com",
    "gcp-sa-cloudiot.iam.gserviceaccount.com",
    "gcp-sa-cloudkms.iam.gserviceaccount.com",
    "gcp-sa-lifesciences.iam.gserviceaccount.com",
    "gcp-sa-logging.iam.gserviceaccount.com",
    "gcp-sa-mi.iam.gserviceaccount.com",
    "cloud-memcache-sa.iam.gserviceaccount.com",
    "cloud-redis.iam.gserviceaccount.com",
    "gcp-sa-networkmanagement.iam.gserviceaccount.com",
    "gcp-sa-pubsub.iam.gserviceaccount.com",
    "gcp-sa-riskmanager.iam.gserviceaccount.com",
    "gcp-sa-cloud-sql.iam.gserviceaccount.com",
    "gcp-sa-cloud-sql.iam.gserviceaccount.com",
    "gcp-sa-cloudscheduler.iam.gserviceaccount.com",
    "gcp-sa-scc-notification.iam.gserviceaccount.com",
    "security-center-api.iam.gserviceaccount.com",
    "sourcerepo-service-accounts.iam.gserviceaccount.com",
    "gcp-sa-spanner.iam.gserviceaccount.com",
    "gcp-sa-firebasestorage.iam.gserviceaccount.com",
    "gcp-sa-cloudtasks.iam.gserviceaccount.com",
    "gcp-sa-cloud-trace.iam.gserviceaccount.com",
    "gcp-sa-translation.iam.gserviceaccount.com",
    "gcp-sa-vmmigration.iam.gserviceaccount.com",
    "gcp-sa-websecurityscanner.iam.gserviceaccount.com",
    "gcp-sa-workflows.iam.gserviceaccount.com",
    "compute-system.iam.gserviceaccount.com",
    "gcp-sa-connectors.iam.gserviceaccount.com",
    "gcp-sa-contactcenterinsights.iam.gserviceaccount.com",
    "container-analysis.iam.gserviceaccount.com",
    "gcp-sa-containerscanning.iam.gserviceaccount.com",
    "gcp-sa-ktd-control.iam.gserviceaccount.com",
    "gcp-sa-dataconnectors.iam.gserviceaccount.com",
    "gcp-sa-datalabeling.iam.gserviceaccount.com",
    "gcp-sa-datapipelines.iam.gserviceaccount.com",
    "gcp-sa-datastudio.iam.gserviceaccount.com",
    "gcp-sa-metastore.iam.gserviceaccount.com",
    "gcp-sa-monitoring.iam.gserviceaccount.com",
    "gcp-sa-dialogflow.iam.gserviceaccount.com",
    "gcp-sa-prod-dai-core.iam.gserviceaccount.com",
    "endpoints-portal.iam.gserviceaccount.com",
    "gcp-sa-eventarc.iam.gserviceaccount.com",
    "gcp-sa-ekms.iam.gserviceaccount.com",
    "gcp-sa-firebaseappcheck.iam.gserviceaccount.com",
    "gcp-sa-firebasemods.iam.gserviceaccount.com",
    "gcp-sa-firebase.iam.gserviceaccount.com",
    "gcp-sa-firebasedatabase.iam.gserviceaccount.com",
    "firebase-rules.iam.gserviceaccount.com",
    "gcp-sa-firewallinsights.iam.gserviceaccount.com",
    "gcp-sa-gsuiteaddons.iam.gserviceaccount.com",
    "gcp-sa-gkehub.iam.gserviceaccount.com",
    "gcp-sa-gameservices.iam.gserviceaccount.com",
    "dataproc-accounts.iam.gserviceaccount.com",
    "Google Cloud Functions Service Agent",
    "cloud-ml.google.com.iam.gserviceaccount.com",
    "gcp-sa-osconfig.iam.gserviceaccount.com",
    "serverless-robot-prod.iam.gserviceaccount.com",
    "containerregistry.iam.gserviceaccount.com",
    "genomics-api.google.com.iam.gserviceaccount.com",
    "gs-project-accounts.iam.gserviceaccount.com",
    "gcp-sa-krmapihosting.iam.gserviceaccount.com",
    "gcp-sa-krmapihosting-dataplane.iam.gserviceaccount.com",
    "gcp-sa-gkenode.iam.gserviceaccount.com",
    "container-engine-robot.iam.gserviceaccount.com",
    "gcp-sa-logging.iam.gserviceaccount.com",
    "gcp-sa-meshconfig.iam.gserviceaccount.com",
    "gcp-sa-monitoring-notification.iam.gserviceaccount.com",
    "gcp-sa-multiclusteringress.iam.gserviceaccount.com",
    "gcp-sa-mcmetering.iam.gserviceaccount.com",
    "gcp-sa-mcsd.iam.gserviceaccount.com",
    "gcp-sa-networkconnectivity.iam.gserviceaccount.com",
    "gcp-sa-ondemandscanning.iam.gserviceaccount.com",
    "gcp-sa-playbooks.iam.gserviceaccount.com",
    "gcp-sa-privateca.iam.gserviceaccount.com",
    "gcp-sa-rbe.iam.gserviceaccount.com",
    "remotebuildexecution.iam.gserviceaccount.com",
    "gcp-sa-retail.iam.gserviceaccount.com",
    "gcp-sa-secretmanager.iam.gserviceaccount.com",
    "gcp-sa-slz.iam.gserviceaccount.com",
    "gcp-sa-vpcaccess.iam.gserviceaccount.com",
    "service-consumer-management.iam.gserviceaccount.com",
    "gcp-sa-servicedirectory.iam.gserviceaccount.com",
    "service-networking.iam.gserviceaccount.com",
    "storage-transfer-service.iam.gserviceaccount.com",
    "cloud-tpu.iam.gserviceaccount.com",
    "gcp-sa-tpu.iam.gserviceaccount.com",
    "gcp-sa-transcoder.iam.gserviceaccount.com",
    "gcp-sa-vmwareengine.iam.gserviceaccount.com",
    "gcp-sa-scc-vmtd.iam.gserviceaccount.com",
]