# simple-web-app

A minimal task list web app (UI plus JSON API) built on the Python standard library. It has no third-party dependencies.

## Run locally

```bash
python app.py
# open http://localhost:8080
```

| Variable   | Default           | Purpose        |
|------------|-------------------|----------------|
| `APP_HOST` | `0.0.0.0`         | Bind address   |
| `APP_NAME` | `Simple Task App` | Page title     |
| `APP_PORT` | `8080`            | Listen port    |

## API

| Method | Path              | Body                  |
|--------|-------------------|-----------------------|
| DELETE | `/api/tasks/{id}` | none                  |
| GET    | `/api/tasks`      | none                  |
| GET    | `/healthz`        | none                  |
| PATCH  | `/api/tasks/{id}` | `{"done": true}`      |
| POST   | `/api/tasks`      | `{"title": "string"}` |

## Container

```bash
docker build -t simple-web-app:1.0.0 .
docker run --rm -p 8080:8080 simple-web-app:1.0.0
```

## Deploy to EKS

1. Push the image to your registry (for example, ECR) and update `image:` in `k8s/simple-web-app.yaml`.
2. Apply and test:

```bash
kubectl apply -f k8s/simple-web-app.yaml
kubectl -n simple-web-app port-forward svc/simple-web-app 8080:80
```

## Constraints

- Tasks are held in memory: they are lost on restart and are not shared across replicas.
- No authentication. Do not expose publicly without adding an auth layer (for example, an ingress with OIDC).
