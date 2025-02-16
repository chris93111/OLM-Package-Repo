import os
import sys

# insert at position 1 in the path, as 0 is the path of this file.
sys.path.insert(1, './../../common_code')

from common_functions import create_overlay
from common_functions import replace_rabbitmq_cluster_operator_version_overlay
from common_functions import replace_rabbitmq_cluster_operator_image
from common_functions import replace_if_rabbitmq_webhook

if len(sys.argv) == 3:
   print('the script needs at least a cluster operator manifests a version and the output directory where store the Bundle as arguments in order to create the OLM structure')
   sys.exit()

operator_release_file = sys.argv[1] 
version = sys.argv[2]
output_directory = sys.argv[3]

# Apply version to the service-version generator
ytt_command_add_version = "ytt -f ./generators/cluster-service-version-generator.yml --data-value-yaml name=rabbitmq-messaging-topology-operator.v"+version+" --data-value-yaml version="+version+ "> ./tmpmanifests/cluster-service-version-generator.yaml"
os.system(ytt_command_add_version)

# Create a copy of the cluster operator and add --- at the end of the file
cluster_operator_release_file = "./generators/cluster-operator.yaml"

os.system("cp " + operator_release_file + " " + cluster_operator_release_file)
os.system("echo \"\n---\" >> "+cluster_operator_release_file )

# Finalize the overlay
create_overlay(cluster_operator_release_file, "kind: Role", "rules:", "---", "./generators/overlay-permission-generator.yaml", "./overlays/overlay-permission.yaml")       
create_overlay(cluster_operator_release_file, "kind: ClusterRole", "rules:", "---", "./generators/overlay-cluster-permission-generator.yaml", "./overlays/overlay-cluster-permission.yaml")    
create_overlay(cluster_operator_release_file, "kind: Deployment", "spec:", "---", "./generators/overlay-deployment-generator.yaml", "./overlays/overlay-deployment.yaml")  
create_overlay(cluster_operator_release_file, "kind: ValidatingWebhookConfiguration", "webhooks:", "---", "./generators/overlay-webhook-generator.yaml", "./overlays/overlay-webhook.yaml")  

replace_rabbitmq_cluster_operator_version_overlay("./overlays/overlay-permission.yaml", "rabbitmq-messaging-topology-operator.v*", "rabbitmq-messaging-topology-operator.v"+version)
replace_rabbitmq_cluster_operator_version_overlay("./overlays/overlay-cluster-permission.yaml", "rabbitmq-messaging-topology-operator.v*","rabbitmq-messaging-topology-operator.v"+version)
replace_rabbitmq_cluster_operator_version_overlay("./overlays/overlay-deployment.yaml", "rabbitmq-messaging-topology-operator.v*", "rabbitmq-messaging-topology-operator.v"+version)
replace_rabbitmq_cluster_operator_version_overlay("./overlays/overlay-webhook.yaml", "rabbitmq-messaging-topology-operator.v*", "rabbitmq-messaging-topology-operator.v"+version)

# Apply the overlay and generate the ClusterServiceVersion file from overlay
os.system("ytt -f ./overlays/overlay-permission.yaml -f ./tmpmanifests/cluster-service-version-generator.yaml  > ./tmpmanifests/cluster-service-version-permission.yaml")
os.system("ytt -f ./overlays/overlay-cluster-permission.yaml -f ./tmpmanifests/cluster-service-version-permission.yaml > ./tmpmanifests/cluster-service-version-cluster-permission.yaml")
os.system("ytt -f ./overlays/overlay-deployment.yaml -f ./tmpmanifests/cluster-service-version-cluster-permission.yaml > ./tmpmanifests/cluster-service-version-webhook.yaml")
os.system("cat ./generators/license.yaml > ./tmpmanifests/rabbitmq.clusterserviceversion.yaml")
os.system("ytt -f ./overlays/overlay-webhook.yaml -f ./tmpmanifests/cluster-service-version-webhook.yaml >> ./tmpmanifests/rabbitmq.clusterserviceversion.yaml")

# Create the bundle structure
rabbitmq_cluster_operator_dir=output_directory+"/" + version 
rabbitmq_cluster_operator_dir_manifests=rabbitmq_cluster_operator_dir+"/manifests"
replace_rabbitmq_cluster_operator_image("./tmpmanifests/rabbitmq.clusterserviceversion.yaml","rabbitmqoperator/messaging-topology-operator:"+version, "docker.io/rabbitmqoperator/messaging-topology-operator:"+version)
os.system("mkdir -p " + rabbitmq_cluster_operator_dir_manifests)
replace_if_rabbitmq_webhook("./tmpmanifests/rabbitmq.clusterserviceversion.yaml")
os.system("cp ./tmpmanifests/rabbitmq.clusterserviceversion.yaml " + rabbitmq_cluster_operator_dir_manifests)
os.system("cp ./manifests_crds/crds/*.yaml " + rabbitmq_cluster_operator_dir_manifests)
os.system("cp ./generators/bundle.Dockerfile " + rabbitmq_cluster_operator_dir)
os.system("cp ./generators/annotations.yaml " + rabbitmq_cluster_operator_dir+"/metadata")
os.system("cp ./generators/rabbitmq.webhook-service.yaml " + rabbitmq_cluster_operator_dir_manifests)
# Cleanup
os.system("rm ./tmpmanifests/*")
os.system("rm ./overlays/*")

# Generate metadata/annotations and Dockerfile
#print(rabbitmq_cluster_operator_dir)
#os.chdir(rabbitmq_cluster_operator_dir)
#os.system("opm alpha bundle generate --directory ./manifests --package rabbitmq-messaging-topology-operator --channels stable --default stable")









