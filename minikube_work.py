from kubernetes import client, config
import subprocess
import random
import paramiko
import os


def get_container_name(container_id): #Получение имени по container_id
    command_name = ['docker', 'ps', '--filter', f'id={container_id}', '--format', '{{.Names}}'] #Получение имени по id
    names_result = subprocess.run(command_name, capture_output=True, text=True)
    if names_result.returncode != 0: #если не успешно
        return None
    container_names=names_result.stdout.strip().split('\n')
    if not container_names:
        return None
    else:
       container_name=random.choice(container_names)
       return container_name

def get_container_pid(dict): #Заполнение словаря pid
    for container_name in dict:
      command_pid = ['docker', 'inspect', '-f', '{{.State.Pid}}', container_name] #получение пид
      result_pid = subprocess.run(command_pid, capture_output=True) #создание процесса, вывод вкл, интерпрет в текст
      if result_pid.returncode == 0: #если успешно
          dict[container_name] = result_pid.stdout.decode().strip() #получение результата
      else:
          dict[container_name] = None #получение результата

def connect_minikube_ssh(dict): #Оптимизировать для несколько node!!!
   ssh = paramiko.SSHClient()
   ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # Добавление ключа хоста (для примера, пропускает проверку ключа)
   # Подключение к Minikube по SSH
   private_key_path = '/home/user/.minikube/machines/minikube/id_rsa' # Вызывается командой: minikube ssh-key
   ip_adress_minikube = '192.168.59.100' # вызывается командой: minikube ip (вернет несколько ip, если несколько node)
   username_minikube='docker'

   ssh.connect(ip_adress_minikube, username=username_minikube, key_filename=private_key_path)
   print('Connect ssh_Minikube:')
   for value in dict.values():
      stdin, stdout, stderr = ssh.exec_command(f'cat /proc/{value}/cgroup')
      output = stdout.read().decode('utf-8')
      print(output)
      print('---------------------')
   ssh.close()
   #print('---------------------')

config.load_kube_config()
v1 = client.CoreV1Api()

nodes = v1.list_node().items
containers = []
kol =0
Name_Pid = {}
    # Выведите информацию о каждой ноде
for node in nodes:
     print(f"Node Name: {node.metadata.name}")
     # Дополнительная информация о ноде
     print(f"Node IP: {node.status.addresses[0].address}")
     print(f"Node OS: {node.status.node_info.operating_system}")
     node_name = node.metadata.name
     #pods = v1.list_pod_for_all_namespaces(field_selector=f"spec.nodeName={node.metadata.name}").items
     pods = v1.list_namespaced_pod(
     namespace="default",
     field_selector=f"spec.nodeName={node_name}" ).items

     for pod in pods:
            print(kol)
            kol +=1
            print(f"Pod Name: {pod.metadata.name}")  # Вывод имени пода
            print(f"Pod UID : {pod.metadata.uid}")  # Вывод идентификатора пода
            containers.append(pod.metadata.name)
            container_statuses = pod.status.container_statuses
            if container_statuses:
                for container_status in container_statuses:
                    container_id = container_status.container_id.replace("docker://", "")
                    print(f"Container ID: {container_id}")
            else:
                print("No container information found")

            container_name = get_container_name(str(container_id)) #Получение имени
            if container_name:
               #print(f"Name of container: {container_name}")
               Name_Pid[container_name]= None
            print("-------------------------")

#print(Name_Pid)
get_container_pid(Name_Pid) #Получение Pid по имени / Заполнение словаря
print(Name_Pid)
connect_minikube_ssh(Name_Pid)
