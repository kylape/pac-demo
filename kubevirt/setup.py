#!/usr/bin/env python3

import subprocess
import time
import os
import signal
import sys
import argparse


def run_command(command, check=True, capture_output=False):
    print("+ " + " ".join(command))
    result = subprocess.run(command, check=check, capture_output=capture_output, text=True)
    return result


def kubectl(command, namespace=None, check=True, capture_output=False):
    kubectl_cmd = ["kubectl"]
    if namespace:
        kubectl_cmd.extend(["-n", namespace])
    kubectl_cmd.extend(command if isinstance(command, list) else command.split())
    return run_command(kubectl_cmd, check=check, capture_output=capture_output)


def port_forward(namespace="cdi", service="svc/cdi-uploadproxy", ports="8443:443"):
    process = subprocess.Popen(
        ["kubectl", "-n", namespace, "port-forward", service, ports],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(1)  # Give it a moment to start

    # Check for errors *after* a short sleep, as the process might take a moment to fail
    poll_result = process.poll()
    if poll_result is not None and poll_result != 0:
        print("Port forward failed to start.")
        print(f"Stderr: {process.stderr.read()}")
        return process, False

    return process, True


def install_kubevirt_operators():
    kubectl("create ns kubevirt")
    kubectl("create ns cdi")
    kubectl("create -f operator/kubevirt-operator.yaml", namespace="kubevirt")
    kubectl("create -f operator/cdi-operator.yaml", namespace="cdi")
    time.sleep(3)


def install_kubevirt_crs():
    kubectl("create -f operator/kubevirt-cr.yaml", namespace="kubevirt")
    kubectl("create -f operator/cdi-cr.yaml", namespace="cdi")
    kubectl("wait cdi cdi --for=condition=Available=True --timeout=5m", namespace="cdi")
    kubectl("wait kubevirt kubevirt --for=condition=Available=True --timeout=5m", namespace="kubevirt")


def install_vm(image_path):
    kubectl("create -f vms/vm-rhel.yaml")
    kubectl(["patch", "--type", "merge", "-p", '{"spec": {"claimPropertySets": [{"accessModes": ["ReadWriteOnce"], "volumeMode": "Filesystem"}]}}', "StorageProfile", "standard"])

    port_forward_process, port_forward_success = port_forward()

    if not port_forward_success:
        print("Port forward setup failed. Exiting.")
        return

    try:
        time.sleep(1)

        run_command([
            "virtctl", "image-upload", "dv", "rhel",
            "--size=15Gi",
            "--force-bind",
            f"--image-path={image_path}",
            "--uploadproxy-url=https://localhost:8443",
            "--insecure"
        ])
    finally:
        print("Terminating port forward process...")
        port_forward_process.terminate()
        port_forward_process.wait()


def main():
    """
    Main function to execute the kubevirt setup and VM image upload.
    """

    parser = argparse.ArgumentParser(description="Sets up Kubevirt on a Kubernetes cluster.")
    parser.add_argument("--kind-binary", default="~/go/bin/kind", help="Path to the kind binary.")
    parser.add_argument("--image-path", default=os.path.join(os.path.expanduser("~"), "Downloads", "rhel-9.5-x86_64-kvm.qcow2"), help="Path to the VM image (.qcow2 file).")
    parser.add_argument("--create-cluster", action="store_true", help="Create a new kind cluster.")

    args = parser.parse_args()

    kind_bin = args.kind_binary
    image_path = args.image_path
    create_cluster = args.create_cluster

    if create_cluster:
        print("Creating kind cluster...")
        run_command(["sudo", kind_bin, "create", "cluster"])
        result = run_command(["sudo", kind_bin, "get", "kubeconfig"], capture_output=True)
        with open("/tmp/root-kind", "w") as fp:
            fp.write(result.stdout)
        os.environ["KUBECONFIG"] = "/tmp/root-kind"
    else:
        print("Using existing cluster. Ensure KUBECONFIG is set correctly.")

    install_kubevirt_operators()
    install_kubevirt_crs()
    install_vm(args.image_path)


if __name__ == "__main__":
    main()
