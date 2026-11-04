from __future__ import annotations

from dataclasses import dataclass
import importlib
import os
from typing import Any, Protocol


class VCenterCollectionError(RuntimeError):
    pass


@dataclass(frozen=True)
class VCenterConnectionConfig:
    vcenter: str
    credential_ref: str
    project_id: str
    tenant_id: str
    datacenter: str = "DC1"
    username_env: str = "OMNIBRIDGE_VCENTER_USERNAME"
    password_env: str = "OMNIBRIDGE_VCENTER_PASSWORD"


class VCenterInventoryClient(Protocol):
    def collect_inventory(self) -> dict[str, Any]:
        pass


def collect_vcenter_fixture(
    config: VCenterConnectionConfig,
    *,
    client: VCenterInventoryClient | None = None,
) -> dict[str, Any]:
    inventory_client = client or PyVmomiVCenterClient(config)
    fixture = dict(inventory_client.collect_inventory())
    fixture.setdefault("project_id", config.project_id)
    fixture.setdefault("tenant_id", config.tenant_id)
    fixture.setdefault("vcenter", config.vcenter)
    fixture.setdefault("datacenter", config.datacenter)
    return fixture


class PyVmomiVCenterClient:
    def __init__(self, config: VCenterConnectionConfig) -> None:
        self.config = config

    def collect_inventory(self) -> dict[str, Any]:
        username = os.getenv(self.config.username_env)
        password = os.getenv(self.config.password_env)
        if not username or not password:
            raise VCenterCollectionError(
                "vCenter mode requires credentials in "
                f"{self.config.username_env} and {self.config.password_env}."
            )

        try:
            connect_module = importlib.import_module("pyVim.connect")
            pyvmomi = importlib.import_module("pyVmomi")
        except ModuleNotFoundError as error:
            raise VCenterCollectionError(
                "vCenter mode requires pyVmomi to be installed in the collector runtime."
            ) from error

        service_instance = connect_module.SmartConnectNoSSL(
            host=self.config.vcenter,
            user=username,
            pwd=password,
        )
        try:
            vim = pyvmomi.vim
            content = service_instance.RetrieveContent()
            root = content.rootFolder
            clusters = self._objects(content, root, [vim.ClusterComputeResource])
            hosts = self._objects(content, root, [vim.HostSystem])
            datastores = self._objects(content, root, [vim.Datastore])
            networks = self._objects(
                content,
                root,
                [vim.Network, vim.dvs.DistributedVirtualPortgroup],
            )
            vms = self._objects(content, root, [vim.VirtualMachine])
            return {
                "project_id": self.config.project_id,
                "tenant_id": self.config.tenant_id,
                "vcenter": self.config.vcenter,
                "datacenter": self.config.datacenter,
                "clusters": [self._cluster(cluster) for cluster in clusters],
                "hosts": [self._host(host) for host in hosts],
                "datastores": [self._datastore(datastore) for datastore in datastores],
                "networks": [self._network(network) for network in networks],
                "vms": [self._vm(vm) for vm in vms],
            }
        finally:
            connect_module.Disconnect(service_instance)

    def _objects(self, content: Any, root: Any, object_types: list[type]) -> list[Any]:
        view = content.viewManager.CreateContainerView(root, object_types, True)
        try:
            return list(view.view)
        finally:
            view.Destroy()

    def _cluster(self, cluster: Any) -> dict[str, Any]:
        return {
            "moid": _moid(cluster),
            "name": str(getattr(cluster, "name", _moid(cluster))),
        }

    def _host(self, host: Any) -> dict[str, Any]:
        parent = getattr(host, "parent", None)
        return {
            "moid": _moid(host),
            "name": str(getattr(host, "name", _moid(host))),
            "cluster_moid": _moid(parent) if parent is not None else "",
        }

    def _datastore(self, datastore: Any) -> dict[str, Any]:
        summary = getattr(datastore, "summary", None)
        capacity = int(getattr(summary, "capacity", 0) or 0)
        return {
            "moid": _moid(datastore),
            "name": str(getattr(datastore, "name", _moid(datastore))),
            "capacity_gb": max(capacity // (1024**3), 0),
        }

    def _network(self, network: Any) -> dict[str, Any]:
        return {
            "moid": _moid(network),
            "name": str(getattr(network, "name", _moid(network))),
            "vlan": _vlan_id(network),
        }

    def _vm(self, vm: Any) -> dict[str, Any]:
        config = getattr(vm, "config", None)
        hardware = getattr(config, "hardware", None)
        runtime = getattr(vm, "runtime", None)
        host = getattr(runtime, "host", None)
        cluster = getattr(host, "parent", None) if host is not None else None
        guest = getattr(vm, "guest", None)
        devices = list(getattr(hardware, "device", []) or [])
        return {
            "moid": _moid(vm),
            "name": str(getattr(vm, "name", _moid(vm))),
            "cluster_moid": _moid(cluster) if cluster is not None else "",
            "host_moid": _moid(host) if host is not None else "",
            "cpu": int(getattr(hardware, "numCPU", 0) or 0),
            "memory_mb": int(getattr(hardware, "memoryMB", 0) or 0),
            "guest_os": str(getattr(config, "guestId", "unknownGuest") or "unknownGuest"),
            "tools_status": str(getattr(guest, "toolsStatus", "unknown") or "unknown"),
            "snapshot_count": _snapshot_count(getattr(vm, "snapshot", None)),
            "nics": [_nic(device, guest) for device in devices if _is_nic(device)],
            "disks": [_disk(device) for device in devices if _is_disk(device)],
        }


def _moid(obj: Any) -> str:
    return str(getattr(obj, "_moId", "") or getattr(obj, "moid", "") or "")


def _vlan_id(network: Any) -> int:
    config = getattr(network, "config", None)
    default_port_config = getattr(config, "defaultPortConfig", None)
    vlan = getattr(default_port_config, "vlan", None)
    return int(getattr(vlan, "vlanId", 0) or 0)


def _is_nic(device: Any) -> bool:
    return "VirtualEthernetCard" in type(device).__name__


def _is_disk(device: Any) -> bool:
    return "VirtualDisk" in type(device).__name__


def _nic(device: Any, guest: Any) -> dict[str, Any]:
    backing = getattr(device, "backing", None)
    network = getattr(backing, "network", None)
    network_moid = _moid(network) if network is not None else str(
        getattr(backing, "networkName", "")
    )
    return {
        "network_moid": network_moid,
        "ip": _ip_for_mac(guest, str(getattr(device, "macAddress", ""))),
    }


def _disk(device: Any) -> dict[str, Any]:
    backing = getattr(device, "backing", None)
    datastore = getattr(backing, "datastore", None)
    capacity_kb = int(getattr(device, "capacityInKB", 0) or 0)
    return {
        "datastore_moid": _moid(datastore) if datastore is not None else "",
        "size_gb": max(capacity_kb // (1024 * 1024), 1),
    }


def _ip_for_mac(guest: Any, mac_address: str) -> str:
    for net in getattr(guest, "net", []) or []:
        if str(getattr(net, "macAddress", "")).lower() != mac_address.lower():
            continue
        ip_addresses = list(getattr(net, "ipAddress", []) or [])
        return str(ip_addresses[0]) if ip_addresses else ""
    return ""


def _snapshot_count(snapshot: Any) -> int:
    root_snapshots = list(getattr(snapshot, "rootSnapshotList", []) or [])
    return sum(_snapshot_tree_count(root) for root in root_snapshots)


def _snapshot_tree_count(snapshot_tree: Any) -> int:
    children = list(getattr(snapshot_tree, "childSnapshotList", []) or [])
    return 1 + sum(_snapshot_tree_count(child) for child in children)
