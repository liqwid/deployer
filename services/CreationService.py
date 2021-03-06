from dataclasses import replace

from clients.k8s import NamespaceClient, ResourceQuotaClient, VolumeClaimClient, DeploymentClient, ServiceClient
from models.QuestDbDeployment import QuestDbDeployment
from models.k8s.deployment.K8sDeploymentConfig import K8sDeploymentConfig
from models.k8s.resource_quota.K8sResourceQuotaConfig import K8sResourceQuotaConfig
from models.k8s.volume_claim.K8sVolumeClaimConfig import K8sVolumeClaimConfig
from repositories import QuestDbDeploymentRepo


async def create(deployment: QuestDbDeployment) -> QuestDbDeployment:
    deployment = await create_namespace(deployment)
    deployment = await create_resource_quota(deployment)
    deployment = await create_volume_claim(deployment)
    deployment = await create_deployment(deployment)
    return await create_service(deployment)


async def create_namespace(deployment: QuestDbDeployment) -> QuestDbDeployment:
    namespace = await NamespaceClient.create(str(deployment.id))
    return await QuestDbDeploymentRepo.update_metadata(deployment.id,
                                                       replace(deployment.k8s_metadata, namespace=namespace))


async def create_resource_quota(deployment: QuestDbDeployment) -> QuestDbDeployment:
    quota_config = K8sResourceQuotaConfig(memory="1Gi", cpu="2")
    resource_quota = await ResourceQuotaClient.create(deployment.k8s_metadata.namespace.name, quota_config)
    return await QuestDbDeploymentRepo.update_metadata(deployment.id,
                                                       replace(deployment.k8s_metadata, resource_quota=resource_quota))


async def create_volume_claim(deployment: QuestDbDeployment) -> QuestDbDeployment:
    claim_config = K8sVolumeClaimConfig("1Gi")
    claim = await VolumeClaimClient.create(deployment.k8s_metadata.namespace.name, claim_config)
    return await QuestDbDeploymentRepo.update_metadata(deployment.id,
                                                       replace(deployment.k8s_metadata, volume_claim=claim))


async def create_deployment(deployment: QuestDbDeployment) -> QuestDbDeployment:
    deployment_config = K8sDeploymentConfig(
        cpu=deployment.k8s_metadata.resource_quota.config.cpu,
        memory=deployment.k8s_metadata.resource_quota.config.memory,
        claim_name=deployment.k8s_metadata.volume_claim.id,
    )
    k8s_deployment = await DeploymentClient.create(deployment.k8s_metadata.namespace.name, deployment_config)
    return await QuestDbDeploymentRepo.update_metadata(deployment.id,
                                                       replace(deployment.k8s_metadata, deployment=k8s_deployment))


async def create_service(deployment: QuestDbDeployment) -> QuestDbDeployment:
    service = await ServiceClient.create(deployment.k8s_metadata.namespace.name)
    return await QuestDbDeploymentRepo.update_metadata(deployment.id,
                                                       replace(deployment.k8s_metadata, service=service))
