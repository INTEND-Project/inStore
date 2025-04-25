# Infrastucture Setup for Instore

This directory contains Kubernetes manifests used to deploy and configure the storage backends that InStore can interact with.

## Structure

### minio/

Contains the manifests to deploy a standalone MinIO instance. This acts as an object store that InStore can manipulate.

### nginx-minio-gateway/

Sets up an NGINX reverse proxy that sits in front of MinIO. This acts as a Cache to emulate a CDN environment.

## Setup

1. **Deploy MinIO**

```bash
kubectl apply -f minio/minio-dev.yaml
```

This deploys a MinIO pod in the `minio-dev` namespace and creates:

- A **NodePort** service exposing the MinIO Console on port `30076` and the MinIO S3 API on port `30077`.
- A **ClusterIP** service exposing MinIO internally to other pods at:  
  `minio-internal.minio-dev.svc.cluster.local:9000`.

2. **Deploy NGINX MinIO Gateway**

```bash
kubectl apply -f nginx-minio-gateway/nginx-minio-gateway.yaml
```


This creates:

- A **Deployment** for NGINX in the `default` namespace.
- A **ConfigMap** with environment variables used by NGINX to proxy MinIO.  
  Update the ConfigMap accordingly.
- A **NodePort** service exposing NGINX on port `30080`.
