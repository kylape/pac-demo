#!/bin/bash

kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo Waiting for Argo CD to complete installation...
kubectl -n argocd wait --for=condition=Available deploy/argocd-server --timeout=120s
kubectl -n argocd wait --for=condition=Available deploy/repo-server --timeout=120s

kubectl wait --for=condition=Established crd/applications.argoproj.io --timeout=1s
kubectl -n argocd create -f argocd.yaml

echo Waiting for Argo CD applications to be applied...
sleep 5
kubectl -n argocd  wait --for=jsonpath='{.status.health.status}'=Healthy app/argocd
sleep 5
kubectl -n argocd  wait --for=jsonpath='{.status.health.status}'=Healthy app/operator-manager

echo Waiting for Stackrox Operator to deploy...
sleep 5
kubectl -n stackrox-operator wait --for=condition=Available deploy/stackrox-operator --timeout=120s

echo Waiting for Central to deploy...
kubectl -n argocd    wait --for=jsonpath='{.status.health.status}'=Healthy app/stackrox-central
kubectl -n stackrox  wait --for=condition=Deployed=True central/stackrox-central-services --timeout=120s
kubectl -n stackrox  wait --for=condition=Available deploy/central-db --timeout=600s
kubectl -n stackrox  wait --for=condition=Available deploy/central --timeout=120s
kubectl -n stackrox  wait --for=condition=Available deploy/config-controller --timeout=120s

echo Waiting for policies to reconcile...
sleep 5
kubectl -n argocd  wait --for=jsonpath='{.status.health.status}'=Healthy app/stackrox-policies
kubectl -n argocd  wait --for=jsonpath='{.status.accepted}'=true app/argocd

echo Argo CD admin password: $(kubectl -n argocd get secret argocd-initial-admin-secret -o json | jq -r '.data.password' | base64 -d)
