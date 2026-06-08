"""Network root resolution and path wiring for Mycelium."""

from network.paths import (
    NetworkPaths,
    apply_network_paths,
    framework_root,
    legacy_network_root,
    network_display_name,
    network_metadata,
    resolve_network_root,
    runtime_path,
    shell_export_network_paths,
)
from network.create import CreateNetworkResult, create_network
from network.introspection import (
    NetworkStatusSummary,
    build_network_capabilities,
    build_network_status,
    format_category_examples,
    format_mcp_instructions,
    format_status_demo,
    format_status_human,
    format_status_verbose,
    status_to_dict,
)
from network.ontology import (
    OntologyGenerationError,
    SkeletonOntologyResult,
    generate_skeleton_ontology,
)
from network.registry import (
    NetworkEntry,
    list_networks,
    load_network_registry,
    register_network,
    set_default_network,
)

__all__ = [
    "CreateNetworkResult",
    "NetworkEntry",
    "NetworkPaths",
    "create_network",
    "apply_network_paths",
    "OntologyGenerationError",
    "SkeletonOntologyResult",
    "NetworkStatusSummary",
    "build_network_capabilities",
    "build_network_status",
    "format_mcp_instructions",
    "format_category_examples",
    "format_status_demo",
    "format_status_human",
    "format_status_verbose",
    "status_to_dict",
    "framework_root",
    "generate_skeleton_ontology",
    "legacy_network_root",
    "list_networks",
    "load_network_registry",
    "network_display_name",
    "network_metadata",
    "register_network",
    "resolve_network_root",
    "runtime_path",
    "set_default_network",
    "shell_export_network_paths",
]
