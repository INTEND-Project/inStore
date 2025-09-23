# Storage Controller

This directory contains contains all the code for the storage controller as of 29/07/2025

## Structure

### API/

Contains the API and scheduler code and docker file for the Sotrage Controller 

### scyllaDB/
The file to run default scyllaDB database 


### backend/

task execute code

## Setup

1. **ScyllaDB Deployment**
  Can be deployed on docker or on kubernetes  

  Docker
    ```bash
    docker pull scylladb/scylla
    ```
    then run the database detached
    
     ```bash
    docker run --name some-scylla -d scylladb/scylla
    ```

  Kubernetes 
    ```bash
    kubectl apply -f scyllaDB.yaml 
    ```
    then run service 

    ```bash
    kubectl apply -f svc-scyllaDB.yaml 
    ```
    
  container address is scylla-service.scylla.svc.cluster.local. 
  more infor on scylla deployment -> https://medium.com/@anandanand7414/scylladb-on-kubernetes-a272132c0fa7
  
  This runs a blank default version of scyllaDB the database for storage controller is created when API is run.


2. **Deployment API**

  Docker

    ```bash
    docker pull michalsworz/storage-controller:v4.2
    ```
   then run it 

    ```bash
    docker run -d -p 5000:5000 michalsworz/storage-controller:v4.2
    ```

  the structure of the call/request is in  API_call.py.
  This creates the database and adds data to it.

  Kubernetes
    Run the yaml file in the kubernetes folder 
    
    the ip to send the request to is 
    "https://node-ip:30500/LoadData"

  3. **Task Executer**

    The second part of the Task Executer can be rewritten to match teh storage environment(Where the if statements are)

    Docker
        If run on Docker create a new build due with the correct addresses for storage and scylla address
        Then run the container 
            "docker run -d  michalsworz/taskexecuter:v(fill in the version you are running)"

    Kubernetes 
        Run the yaml
        

