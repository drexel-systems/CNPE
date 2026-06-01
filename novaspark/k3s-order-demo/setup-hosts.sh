#!/usr/bin/env bash
##
## setup-hosts.sh — add / update the orders.local entry in /etc/hosts
##
## Usage:
##   ./setup-hosts.sh          # auto-detect cluster IP from kubectl
##   ./setup-hosts.sh <IP>     # use a specific IP (handy if kubectl isn't local)
##
## Requires: kubectl on PATH (or pass IP manually), sudo for /etc/hosts writes.
##

set -euo pipefail

HOSTNAME="orders.local"
HOSTS_FILE="/etc/hosts"

## ── 1. Resolve cluster IP ────────────────────────────────────────────────────

if [[ $# -ge 1 ]]; then
    CLUSTER_IP="$1"
    echo "Using provided IP: ${CLUSTER_IP}"
else
    echo "Looking up cluster node IP from kubectl..."

    if ! command -v kubectl &>/dev/null; then
        echo "ERROR: kubectl not found. Install kubectl or pass the IP as an argument:" >&2
        echo "  ./setup-hosts.sh <IP>" >&2
        exit 1
    fi

    # Get the INTERNAL-IP of the first Ready node.
    # 'kubectl get nodes -o wide' output:
    #   NAME   STATUS   ROLES   AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   ...
    CLUSTER_IP=$(kubectl get nodes -o wide --no-headers 2>/dev/null \
        | awk '$2=="Ready" {print $6; exit}')

    if [[ -z "${CLUSTER_IP}" ]]; then
        # Fallback: grab the first node regardless of status
        CLUSTER_IP=$(kubectl get nodes -o wide --no-headers 2>/dev/null \
            | awk 'NR==1 {print $6}')
    fi

    if [[ -z "${CLUSTER_IP}" || "${CLUSTER_IP}" == "<none>" ]]; then
        echo "ERROR: Could not determine cluster IP from kubectl." >&2
        echo "  Run:  kubectl get nodes -o wide" >&2
        echo "  Then: ./setup-hosts.sh <INTERNAL-IP>" >&2
        exit 1
    fi

    echo "Detected cluster IP: ${CLUSTER_IP}"
fi

## ── 2. Validate IP looks sane ────────────────────────────────────────────────

if ! [[ "${CLUSTER_IP}" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "ERROR: '${CLUSTER_IP}' does not look like an IPv4 address." >&2
    exit 1
fi

## ── 3. Update /etc/hosts ─────────────────────────────────────────────────────

ENTRY="${CLUSTER_IP}  ${HOSTNAME}"

if grep -qP "(\s|^)${HOSTNAME}(\s|$)" "${HOSTS_FILE}" 2>/dev/null; then
    # Entry exists — replace the whole line regardless of what IP was there before
    echo "Updating existing ${HOSTNAME} entry in ${HOSTS_FILE}..."
    sudo sed -i -E "s|^[^#]*[[:space:]]${HOSTNAME}([[:space:]].*)?$|${ENTRY}|" "${HOSTS_FILE}"
    echo "  Updated → ${ENTRY}"
else
    # Entry doesn't exist — append
    echo "Appending new entry to ${HOSTS_FILE}..."
    echo "${ENTRY}" | sudo tee -a "${HOSTS_FILE}" > /dev/null
    echo "  Appended → ${ENTRY}"
fi

## ── 4. Verify ────────────────────────────────────────────────────────────────

echo ""
echo "Current ${HOSTNAME} lines in ${HOSTS_FILE}:"
grep "${HOSTNAME}" "${HOSTS_FILE}"

echo ""
echo "Done. You can now reach the API at:"
echo "  curl -s http://${HOSTNAME}/orders"
