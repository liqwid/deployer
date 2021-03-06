from copy import deepcopy

from kubernetes_asyncio.client import V1PersistentVolumeClaim
from kubernetes_asyncio.client.exceptions import ApiException

from models.k8s.volume_claim.K8sVolumeClaim import K8sVolumeClaim
from models.k8s.volume_claim.K8sVolumeClaimConfig import K8sVolumeClaimConfig
from .client import get_core_client
from .templates import volume_claim_template


async def create(namespace: str, config: K8sVolumeClaimConfig) -> K8sVolumeClaim:
    template = deepcopy(volume_claim_template)
    template['metadata']['name'] = f"volume-claim-{namespace}"
    template['spec']['resources']['requests']['storage'] = config.storage
    core_client = get_core_client()
    response: V1PersistentVolumeClaim = await core_client.create_namespaced_persistent_volume_claim(namespace, template)

    return K8sVolumeClaim(id=response.metadata.name, config=config)


async def refresh(namespace: str, claim: K8sVolumeClaim | None) -> K8sVolumeClaim | None:
    if claim is None: return None

    core_client = get_core_client()
    try:
        await core_client.read_namespaced_persistent_volume_claim(claim.id, namespace)
    except ApiException as error:
        if error.status == 404:
            return None
        else: raise error

    return claim
