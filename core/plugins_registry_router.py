"""GET /api/v1/plugins/registry — returns all loaded plugin metadata + MFE remote URLs."""
from fastapi import APIRouter, Request

router = APIRouter(tags=["plugins"])

# Maps plugin name → (path_prefix, exposed_module, federation_name)
_MFE_MAP: dict[str, tuple[str, str, str]] = {
    "snmp":         ("snmp",         "SnmpModule",         "snmpUI"),
    "ves":          ("ves",          "VesModule",          "vesUI"),
    "webhook":      ("webhook",      "WebhookModule",      "webhookUI"),
    "protobuf":     ("protobuf",     "ProtobufModule",     "protobufUI"),
    "avro":         ("avro",         "AvroModule",         "sftpAvroUI"),
    "sftp":         ("sftp",         "SftpModule",         "sftpAvroUI"),
}

# UI-only MFEs — no Python plugin, pure frontend containers.
# These are appended directly so they appear in the sidebar.
_UI_ONLY_MFES = [
    {
        "name":           "fm-console",
        "version":        "1.0.0",
        "domains":        ["FM"],
        "protocols":      [],
        "remote_url":     "/mfe/fm-console/assets/remoteEntry.js",
        "exposed":        "./FmConsoleModule",
        "federation_name": "fmConsole",
        "health":         "healthy",
    },
    {
        "name":           "pm-dashboard",
        "version":        "1.0.0",
        "domains":        ["PM"],
        "protocols":      [],
        "remote_url":     "/mfe/pm-dashboard/assets/remoteEntry.js",
        "exposed":        "./PmDashboardModule",
        "federation_name": "pmDashboard",
        "health":         "healthy",
    },
    {
        "name":           "log-viewer",
        "version":        "1.0.0",
        "domains":        ["LOG"],
        "protocols":      [],
        "remote_url":     "/mfe/log-viewer/assets/remoteEntry.js",
        "exposed":        "./LogViewerModule",
        "federation_name": "logViewer",
        "health":         "healthy",
    },
]


@router.get("/api/v1/plugins/registry")
async def get_plugin_registry(request: Request):
    registry = request.app.state.plugin_registry
    plugins  = []
    for name, plugin in registry.plugins.items():
        meta = plugin.get_metadata()
        path_prefix, module_name, federation_name = _MFE_MAP.get(
            name,
            (name, f"{name.title()}Module", name),
        )
        meta["remote_url"]       = f"/mfe/{path_prefix}/assets/remoteEntry.js"
        meta["exposed"]          = f"./{module_name}"
        meta["federation_name"]  = federation_name
        meta["health"]           = "healthy"
        plugins.append(meta)

    # Append pure-UI MFEs that have no Python plugin counterpart
    plugins.extend(_UI_ONLY_MFES)

    return {"plugins": plugins, "count": len(plugins)}
