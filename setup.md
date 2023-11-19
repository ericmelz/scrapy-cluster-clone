# Setup notes
This document contains step-by-step notes on how to setup scrapy-cluster on
* laptop
* docker-compose
* minikube

We try out each piece of the system before putting it all together

## Redis
### local
```
# terminal 1
redis-server

# terminal 2
redis-cli
keys *
set name eric
get name
^D

# terminal1
^C
```


### docker-compose
```
# Optional if redis isn't installed on local machine
#brew install redis

docker ps
docker-compose up -d
docker ps
redis-cli
keys *
^D
docker-compose down
```

### minikube
```
minikube status
minikube start
minikube status
ls -l k8s|grep redis
cat k8s/redis-deployment.yaml
cat k8s/redis-service.yaml
kubectl get all
kubectl apply -f k8s/redis-deployment.yaml
kubectl get all
kubectl apply -f k8s/redis-service.yaml
kubectl get all
# note pod name, replace pod/** in next cmd
kubectl logs --tail=100 pod/redis-6875d6bdcc-rdlxd

minikube service redis --url # observe port, e.g., might emit port = 61156
redis-cli -p 61156
set foo bar
get foo
^D

kubectl delete svc redis
kubctl get all
kubctl delete deployment redis
```

## Zookeeper

### Local
Installation:
```
brew install zookeeper

To start zookeeper now and restart at login:
  brew services start zookeeper
Or, if you don't want/need a background service you can just run:
  SERVER_JVMFLAGS="-Dapple.awt.UIElement=true" /opt/homebrew/opt/zookeeper/bin/zkServer start-foreground
```

Testing:
```
SERVER_JVMFLAGS="-Dapple.awt.UIElement=true" /opt/homebrew/opt/zookeeper/bin/zkServer start-foreground
# when finished w/client testing (below)
^C

# separate terminal
zkcli -server 127.0.0.1:2181
ls /
create /zk_test my_data
ls /
get /zk_test
^C
```

### docker-compose
```
docker-compose up -d
pid=$(docker ps |grep zoo | cut -d' ' -f 1)
docker logs $pid
zkcli -server 127.0.0.1:2181
ls /
create /zk_test my_data1
ls /
get /zk_test
^C
docker-compose down
```

### k8s
```
ls -l k8s | grep zoo
cat k8s/zookeeper-deployment.yaml
cat k8s/zookeeper-service.yaml
kubectl apply -f k8s/zookeeper-deployment.yaml
kubectl apply -f k8s/zookeeper-service.yaml

# note port
minikube service zookeeper --url

# seperate terminal
zkcli -server 127.0.0.1:62120
ls /
create /zk_test my_data2
ls /
get /zk_test
^C

# original terminal
^C
kubectl delete service zookeeper
```

## Kafka
### local
```
brew install kafka

To start kafka now and restart at login:
  brew services start kafka
Or, if you don't want/need a background service you can just run:
  /opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties


# separate terminal - start zk
SERVER_JVMFLAGS="-Dapple.awt.UIElement=true" /opt/homebrew/opt/zookeeper/bin/zkServer start-foreground

# original terminal - start kafka
/opt/homebrew/opt/kafka/bin/kafka-server-start /opt/homebrew/etc/kafka/server.properties

# third terminal
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic test
kafka-console-producer --broker-list localhost:9092 --topic test
hello
there
dood

# fourth terminal
kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning

# Kill all jobs in all terminals (^C)
```

### docker
```
# see https://stackoverflow.com/questions/25497279/unknownhostexception-kafka
# see https://rmoff.net/2018/08/02/kafka-listeners-explained/

# edit /etc/hosts and add
127.0.0.1       kafka

# Terminal 1
docker-compose up -d

# Terminal 2
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic test
kafka-console-producer --broker-list localhost:9092 --topic test
hallo
thar

# terminal 3
kafka-console-consumer --bootstrap-server localhost:9092 --topic test --from-beginning

# quit out ot terminal 2 and terminal 3 (^C)

In Terminal 1:
docker-compose down
```

### minikube
```
# terminal 1
kubectl apply -f k8s/zookeeper-deployment.yaml
kubectl apply -f k8s/zookeeper-service.yaml

kubectl apply -f k8s/kafka-claim0-persistentvolumeclaim.yaml
kubectl apply -f k8s/kafka-deployment.yaml
kubectl logs pod/kafka-576cd774f8-4ss2j # substitute actual pod (from kubectl get pod)
kubectl apply -f k8s/kafka-service.yaml

# optional
#kubectl exec -it kafka-576cd774f8-4ss2j -- bash

kubectl port-forward --address 0.0.0.0 service/kafka 9092:9092
kafka-topics --create --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1 --topic testing
kafka-console-producer --broker-list localhost:9092 --topic testing
yo
mamma

# terminal 2
kafka-console-consumer --bootstrap-server localhost:9092 --topic testing --from-beginning
```

## Rest of crawler

### k8s
This requires a special docker build due to modifications:
```
kubectl delete deployment redis-monitor
minikube ssh
docker images
docker rmi ericmelz/eric-redis-monitor:latest
docker rmi ericmelz/eric-kafka-monitor:latest
docker rmi ericmelz/eric-crawler:latest
docker rmi ericmelz/eric-crawler-rest:latest
docker images
^D

docker build -t ericmelz/eric-redis-monitor:latest -f docker/redis-monitor/Dockerfile.py3 .
docker build -t ericmelz/eric-kafka-monitor:latest -f docker/kafka-monitor/Dockerfile.py3 .
docker build -t ericmelz/eric-crawler:latest -f docker/crawler/Dockerfile.py3 .
docker build -t ericmelz/eric-crawler-rest:latest -f docker/rest/Dockerfile.py3 .
docker push ericmelz/eric-redis-monitor:latest
docker push ericmelz/eric-kafka-monitor:latest
docker push ericmelz/eric-crawler:latest
docker push ericmelz/eric-crawler-rest:latest
```


Start in the k8s state for kafka, namely the following service should be up in minikube:
- zookeeper
- kafka

Note the redis-monitor has been modified from the original to avoid env conflicts with k8s.
```
# deploy redis
kubectl apply -f k8s/redis-deployment.yaml
kubectl apply -f k8s/redis-service.yaml

# deploy redis-monitor
kubectl apply -f k8s/redis-monitor-deployment.yaml

# examine logs - should have some output
pod=$(kubectl get pods|grep redis-monitor|cut -d' ' -f 1)
kubectl logs $pod

# run tests
kubectl exec -it $pod -- bash
./run_docker_tests.sh
^D

# deploy kafka-monitor
kubectl apply -f k8s/kafka-monitor-deployment.yaml

# examine logs - should have some output
pod=$(kubectl get pods|grep kafka-monitor|cut -d' ' -f 1)
kubectl logs $pod

# run tests
kubectl exec -it $pod -- bash
./run_docker_tests.sh
^D

# deploy crawler
kubectl apply -f k8s/crawler-deployment.yaml

# examine logs - should have some output
pod=$(kubectl get pods|grep crawler|cut -d' ' -f 1)
kubectl logs $pod

# run tests
kubectl exec -it $pod -- bash
./run_docker_tests.sh
^D

# deploy rest
kubectl apply -f k8s/rest-deployment.yaml
kubectl apply -f k8s/rest-service.yaml

# examine logs - should have some output
pod=$(kubectl get pods|grep rest|cut -d' ' -f 1)
kubectl logs $pod

# run tests
kubectl exec -it $pod -- bash
./run_docker_tests.sh
^D

```

## Test crawl
```
# Terminal 1 - crawl results
pod=$(kubectl get pods|grep kafka-monitor|cut -d' ' -f 1)
kubectl exec -it $pod -- bash
python kafkadump.py dump -t demo.crawled_firehose

# Terminal 2 - action results
pod=$(kubectl get pods|grep kafka-monitor|cut -d' ' -f 1)
kubectl exec -it $pod -- bash
python kafkadump.py dump -t demo.outbound_firehose

# Terminal 3 - crawler
pod=$(kubectl get pods|grep crawler|cut -d' ' -f 1)
kubectl exec -it $pod -- bash
scrapy runspider crawling/spiders/link_spider.py

# Terminal 4 - commands
pod=$(kubectl get pods|grep kafka-monitor|cut -d' ' -f 1)
kubectl exec -it $pod -- bash
python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"abc123"}'
```

You should see crawl results come out in terminal 1
See [scrapy-crawler quickstart](https://scrapy-cluster.readthedocs.io/en/latest/topics/introduction/quickstart.html) for more tests.

## Simplified setup
### AWS auth
Create ECR repos, 1 per docker image

In AWS create an IAM user with ECR access to your repos
Attach the following managed policies to the user:
- arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
- arn:aws:iam::aws:policy/AmazonElasticContainerRegistryPublicFullAccess

Create an AWS_ACCESS_KEY_ID and AWS_SECRET_KEY for the user
install awscli locally:
```
brew install awscli
aws configure
# type access key, secret key, etc
```

Put ECR login into eks as a secret:
```
ECR_PASSWORD=$(aws ecr get-login-password --region us-east-1)
kubectl create secret docker-registry ecr-secret --docker-server=638173936794.dkr.ecr.us-east-1.amazonaws.com --docker-username=AWS --docker-password="${ECR_PASSWORD}"
```

```
minikube start

kubectl apply -f k8s/zookeeper-deployment.yaml
kubectl wait --for=condition=available --timeout=30s deployment/zookeeper
kubectl apply -f k8s/zookeeper-service.yaml
kubectl apply -f k8s/kafka-claim0-persistentvolumeclaim.yaml
kubectl apply -f k8s/kafka-deployment.yaml
kubectl wait --for=condition=available --timeout=30s deployment/kafka
kubectl apply -f k8s/kafka-service.yaml
kubectl apply -f k8s/redis-deployment.yaml
kubectl wait --for=condition=available --timeout=30s deployment/redis
kubectl apply -f k8s/redis-service.yaml
kubectl apply -f k8s/redis-monitor-deployment.yaml
kubectl apply -f k8s/kafka-monitor-deployment.yaml
kubectl apply -f k8s/crawler-deployment.yaml
kubectl apply -f k8s/rest-deployment.yaml
kubectl apply -f k8s/rest-service.yaml
```

# Shutdown
```
kubectl delete svc --all
kubectl delete deploy --all
minikube stop
```

## Simplified test

## Testing k8s features
```
# Terminal 1 - commands
pod=$(kubectl get pods|grep kafka-monitor|cut -d' ' -f 1)
kubectl exec -it $pod -- bash

# Terminal 2 - crawl results
pod=$(kubectl get pods|grep kafka-monitor|cut -d' ' -f 1)
kubectl exec -it $pod -- bash
python kafkadump.py dump -t demo.crawled_firehose

# Terminal 3 - crawler
pod=$(kubectl get pods|grep crawler|cut -d' ' -f 1)
kubectl exec -it $pod -- bash
scrapy runspider crawling/spiders/link_spider.py

# Terminal 1
python kafka_monitor.py feed '{"url": "http://dmoztools.net", "appid":"testapp", "crawlid":"abc123"}'

# watch terminal 2
```

# resilience - kill a crawler

# scaling - add a crawler
```
