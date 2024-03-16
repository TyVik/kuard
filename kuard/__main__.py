import json
import subprocess

from kubernetes import client, config
from kubernetes.client import V1Node, V1Pod
from paramiko.client import SSHClient, AutoAddPolicy

from kuard.types import Pod, Container, Metrics

config.load_kube_config()
v1 = client.CoreV1Api()


def get_nodes() -> list[V1Node]:
    return v1.list_node().items


def get_pods(node: V1Node):
    def collect_pod_containers(pod: V1Pod) -> list[Container]:
        result = []
        for container in pod.status.container_statuses:
            if not container.ready:
                continue  # init-containers

            result.append(Container(
                id=container.container_id.split("//")[-1],
                name=container.name
            ))
        return result

    def collect_pod_info(pod: V1Pod) -> Pod:
        containers = collect_pod_containers(pod)
        return Pod(
            name=pod.metadata.name,
            uid=pod.metadata.uid,
            containers=containers
        )

    # здесь можно запрашивать по всем именам и парсить, потом переделаем
    pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node.metadata.name}").items
    return [collect_pod_info(pod) for pod in pods]


def get_ip(node: V1Node) -> str:
    internal = next(address for address in node.status.addresses if address.type == "InternalIP")
    return internal.address


def get_ssh_to_node(ip: str) -> SSHClient:
    def get_private_key_for_ip(ip) -> str:
        command = ['minikube', 'ssh-key']
        completed = subprocess.run(command, capture_output=True)
        return completed.stdout.decode().strip()

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())  # Добавление ключа хоста (для примера, пропускает проверку ключа)
    private_key_file = get_private_key_for_ip(ip)
    ssh.connect(ip, username='docker', key_filename=private_key_file)
    return ssh


def collect_metrics(ssh: SSHClient, inspect) -> Metrics:
    def get_files_count(ssh: SSHClient, overlay: str) -> int:
        stdin, stdout, stderr = ssh.exec_command(f"sudo su -c 'find {overlay} -type d -o -type f | wc -l'")
        output = stdout.read().decode('utf-8')
        return int(output)

    result = {}
    result["files_count"] = get_files_count(ssh, inspect[0]["GraphDriver"]["Data"]["UpperDir"])
    return result


if __name__ == "__main__":
    nodes = get_nodes()
    state = {get_ip(node): get_pods(node) for node in nodes}

    for node, pods in state.items():
        ssh = get_ssh_to_node(node)
        for pod in pods:
            for container in pod["containers"]:
                stdin, stdout, stderr = ssh.exec_command(f"docker inspect {container['id']}")
                output = stdout.read().decode('utf-8')
                container["inspect"] = json.loads(output)
                container["metrics"] = collect_metrics(ssh, container["inspect"])

    print(json.dumps(state, indent=2))
