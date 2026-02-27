"""GET /api/v1/plugins/registry — returns all loaded plugin metadata + MFE remote URLs."""
from fastapi import APIRouter, Request

router = APIRouter(tags=["plugins"])

# Maps plugin name → (container path prefix, exposed module name)
# sftp and avro share one container (sftp-avro-ui) but expose two modules.
_MFE_MAP: dict[str, tuple[str, str]] = {
    "snmp":     ("snmp",    "SnmpModule"),
    "ves":      ("ves",     "VesModule"),
    "webhook":  ("webhook", "WebhookModule"),
    "protobuf": ("protobuf","ProtobufModule"),
    "avro":     ("avro",    "AvroModule"),
    "sftp":     ("sftp",    "SftpModule"),
    # FCAPS-domain MFEs
    "fm-console":   ("fm-console",  "FmConsoleModule"),
    "pm-dashboard": ("pm-dashboard","PmDashboardModule"),
    "log-viewer":   ("log-viewer",  "LogViewerModule"),
}


@router.get("/api/v1/plugins/registry")
async def get_plugin_registry(request: Request):
    registry = request.app.state.plugin_registry
    plugins  = []
    for name, plugin in registry.plugins.items():
        meta = plugin.get_metadata()
        path_prefix, module_name = _MFE_MAP.get(name, (name, f"{name.title()}Module"))
        meta["remote_url"] = f"/mfe/{path_prefix}/assets/remoteEntry.js"
        meta["exposed"]    = f"./{module_name}"
        meta["health"]     = "healthy"
        plugins.append(meta)
    return {"plugins": plugins, "count": len(plugins)}
