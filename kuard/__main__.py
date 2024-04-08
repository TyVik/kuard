import json
import os
import base64
from kubernetes import client, config
from kubernetes.client import V1Node, V1Pod
import tempfile

from paramiko.client import SSHClient, AutoAddPolicy

from kuard.alerts import notify
from kuard.class_types import Pod, Container, Metrics

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


def get_ssh_to_node(ip: str, private_key_str: str) -> SSHClient:
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())  # Добавление ключа хоста (для примера, пропускает проверку ключа)

    with tempfile.NamedTemporaryFile(delete=False) as key_file:
        key_file.write(private_key_str.encode())
        private_key_path = key_file.name
    ssh.connect(ip, username='docker', key_filename=private_key_path)
    return ssh


def collect_metrics(ssh: SSHClient, inspect) -> Metrics:
    def get_files_count(ssh: SSHClient, overlay: str) -> int:
        stdin, stdout, stderr = ssh.exec_command(f"sudo su -c 'find {overlay} -type d -o -type f | wc -l'")
        output = stdout.read().decode('utf-8')
        return int(output)

    def get_cpu(ssh: SSHClient, container_id: str) -> int:
        stdin, stdout, stderr = ssh.exec_command(f"docker stats --no-stream --format '{{{{.CPUPerc}}}}' {container_id}")
        output = stdout.read().decode('utf-8').rstrip('%\n')
        return float(output)

    def get_memory(ssh: SSHClient, container_id: str) -> str:
        stdin, stdout, stderr = ssh.exec_command(f"docker stats --no-stream --format '{{{{.MemUsage}}}}' {container_id}")
        output = stdout.read().decode('utf-8').rstrip('%\n')
        return str(output)

    result = {}
    result["files_count"] = get_files_count(ssh, inspect[0]["GraphDriver"]["Data"]["UpperDir"])
    result["CPU"] = get_cpu(ssh, inspect[0]["Id"])
    result["memory"] = get_memory(ssh, inspect[0]["Id"])
    return result


def check_rules(container: Container):
    files_count = container["metrics"]["files_count"]
    if files_count > 10:
        notify(f"B {container['name']} большое количество файлов! ({files_count})")


if __name__ == "__main__":
    nodes = get_nodes()
    state = {get_ip(node): get_pods(node) for node in nodes}
    ssh_keys = json.loads(base64.b64decode(os.environ.get('IP_SSH')).decode())
    for node, pods in state.items():
        ip = list(ssh_keys.keys())[0]
        ssh_key = ssh_keys[ip]
        ssh = get_ssh_to_node(ip, ssh_key)
        for pod in pods:
            for container in pod["containers"]:
                stdin, stdout, stderr = ssh.exec_command(f"docker inspect {container['id']}")
                output = stdout.read().decode('utf-8')
                container["inspect"] = json.loads(output)
                container["metrics"] = collect_metrics(ssh, container["inspect"])
                check_rules(container)

    #print(json.dumps(state, indent=2))
