# Infrastucture Setup for Instore

This directory contains Kubernetes manifests used to deploy and configure the storage backends that InStore can interact with.

## Structure

### minio/

Contains the manifests to deploy a standalone MinIO instance. This acts as an object store that InStore can manipulate.

### nginx-minio-gateway/

Sets up an NGINX reverse proxy that sits in front of MinIO. This acts as a Cache to emulate a CDN environment.

### coreDNS/

Sets up coreDNS to resolve our self-hosted cdn domain name `cdn.test` to the IP addresses of available nginx gateways.

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

    You may deploy an Nginx MinIO Gateway on as many clusters as needed for your experiment. You just need to make sure to point back to the MinIO origin using nodeport service.

3. **Deploy CoreDNS**

    Your working directory should be `./coreDNS`

    Get yourself one of the [pre-built coreDNS binaries](https://github.com/coredns/coredns/releases/latest) or build from [source](https://github.com/coredns/coredns#compilation-from-source) then run with: 

    ```bash
    ./coredns -dns.port 1053
    ```

    By default coredns picks up its configuration from the `Corefile` in the current directory. Otherwise, you can pass configuration by using the `-conf` flag.

    As of now, we read the records for our domain name `cdn.test` from the zone file `db.cdn.test`. The IP addresses of all the available Nginx gateways should be in there. Update the file before running the dns server.

    To use coreDNS for DNS resolution in your envionment, you will need to create a `reslove.conf` override by creating a drop-in override directory in `/etc/systemd` and placing your `coredns.conf` in there then restarting `system-resolved.service`. To go back to the default stub resolver after you're done you will just need to delete the directory you created and restart the system-resolved service again.

    ```bash
    sudo mkdir -p /etc/systemd/resolved.conf.d
    sudo cp ./coredns.conf /etc/systemd/resolved.conf.d/
    sudo systemctl restart systemd-resolved
    sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    ```
    Then confirm with:
    ```bash
    resolvectl status
    ```
4. **Test Your Setup**

    To test your self-host CDN setup you will need to create a bucket in MinIO and place the files you want to fetch in there. Create a key and secret and configure your Nginx instances to use those credentials and to proxy the bucket. Now, having configured coreDNS with the IP addresses of your Nginx gateways and set it up for DNS resolution. Try curling your files:

    ```bash
    curl -I cdn.test:30080/filename
    ```