install:
	pip install -r requirements.txt

active:
	eval $(minikube -p minikube docker-env)

run:
	python3 -m kuard
