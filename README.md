# ACS Policy as Code Demo Repo

Install Argo CD
```
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd get secret argocd-initial-admin-secret -o json | jq -r '.data.password' | base64 -d
```

Install Argo CD resources
```
kubectl create -f argocd.yaml
```

## Potential Argo CD demos

* Create a policy from scratch using `kubectl explain` to guide an author
* Check in a custom policy saved as a CR from the Central UI
* Edit a policy, commit, push, and observe the change in Kubernetes and Central
* Check in an invalid policy: 1) caught by schema validation, 2) caught by Central
* Demo potential CI validations: 1) Dry run against K8s; 2) Dry run against Central
* Use Kustomize to create per-environment policy overlays (e.g. dev and prod)
