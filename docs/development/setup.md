# Setting up the development environment

## Requirements

You must have the following installed in the development environment:

- docker
- python
- go
- [kind](https://kind.sigs.k8s.io/)
- kubectl
- [helm](https://helm.sh/docs/intro/install/)

## Install Python packages

Run

```
> scripts/install
```

to install the packages into a virtualenv (note: activate the virtualenv beforehand.) You should run this even if you are only doing docker development, otherwise the python eggs installed into the container will be overridden by volume mounts.

## Set up development environment

Run

```
> scripts/setup
```

To build set up the development cluster, build docker images,
and set up test data.

You can run `scripts/update` to build the docker images and update dependencies
at any time. Add the `--help` flag to see the available options targeting
subsets of images.


http://localhost:8500

## Bring up development servers

To run the development servers:

```
> scripts/server
```

This will start Azurite, a PgSTAC database, the Azure Functions server, a local executor for testing, a stac-fastapi
to inspect ingest results, and the frontend.

| Service           | URL                          |
| ----------------- | ---------------------------- |
| PC Tasks API      | <http://localhost:8511/runs> |
| PC Tasks Frontend | <http://localhost:8515>      |
| STAC API          | <http://localhost:8513>      |
| STAC Browser      | <http://localhost:8514>      |

You can avoid building or bringing up the STAC API and STAC Browser
servers by using the flag `--no-aux-servers` in `scripts/setup`,
`scripts/update`, and `scripts/server`. This can save on build time
and memory footprint if you are not using those services.

## Bring up the development Kind cluster

If you are using the development cluster, use the `scripts/cluster` script to manage the cluster:

```
# Create cluster, install Helm charts, publish relevant docker images to local registry:
scripts/cluster setup
# Update the helm charts and images
scripts/cluster update
# Get an Argo token that can be used to log into the Argo UI
scripts/cluster argo-token
# Destroys and recreates the cluster
scripts/cluster recreate
# Deletes the cluster
scripts/cluster delete
```

Clusters are ephemeral, and can take up significant resources; it is fine to run `scripts/cluster delete` and `scripts/cluster create` as needed.

## Setting up local secrets

PCTasks uses a docker container run via `docker-compose`, brought up by `scripts/server`, to mock the functionality of KeyVault for fetching secrets.
It will return any secret that is contained in the `dev-secrets.yaml` file in the root directory of the repository.

To create secrets, copy `dev-secrets.template.yaml` to `dev-secrets.yaml`, and fill in any key/value pairs
you need for secrets, e.g. the `tenant-id`, `client-id`, and `client-secret` for our Azure service principal.

## Testing

Run

```
> scripts/test
```

to test. You can also run `scripts/format` to format code. Use `--help` to see options on any script.

### Kubernetes config

You can export a kubeconfig for `kubectl`

```
> kind export kubeconfig --name kind-pctasks
```

## Frontend Settings

The frontend is configured with default values to connect to and authenticate with the local PCTasks API server. If you want to use a remote API, like staging or test, you'll need to override a few settings. You can do this by modifying the `.env` file in the root `pctasks_frontend` project directory which was created during `scripts/setup`. If you do not have this file, you can manually copy the `.env.sample` file to `.env`.

| Variable                      | Description                                                                                           | Default                 |
|-------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------|
| REACT_APP_IS_DEV              | Whether the frontend is running in development mode and using a dev-only auth token for API requests. | true                    |
| REACT_APP_API_ROOT            | The root of the API endpoint to use for requests.                                                     | <http://localhost:8511> |
| REACT_APP_DEV_AUTH_TOKEN      | The dev-only auth token to use for API requests.                                                      | hunter2                 |
| REACT_APP_AUTH_TENANT_ID      | The tenant ID to use for API requests.                                                                | --                      |
| REACT_APP_AUTH_CLIENT_ID      | The client ID to use for API requests.                                                                | --                      |
| REACT_APP_AUTH_BACKEND_APP_ID | The backend App ID that exposes API scopes via the frontend App Registration.                         | --                      |

**Note:** The `REACT_APP_AUTH_*` variables are used to establish an oAuth2 flow against a registered Azure AD application. You'll need to get these values from the Azure AD portal for the target environment. These values can remain unset when `REACT_APP_IS_DEV` is set to true.

## Argo UI

Once the kind cluster is up, you can view the Argo UI by visiting http://localhost:8500/argo.
You'll need to use your ARGO_TOKEN to log in, which you can
find using `scripts/cluster argo-token`
