"""GET /api/v1/plugins/registry — returns all loaded plugin metadata + MFE remote URLs."""
from fastapi import APIRouter, Request

router = APIRouter(tags=["plugins"])

# Maps plugin name → (path_prefix, exposed_module, federation_name)
# federation_name MUST exactly match `name` in each MFE's vite.config.ts federation() call.
# That is the key Vite uses to register the container on window.<federation_name>.
_MFE_MAP: dict[str, tuple[str, str, str]] = {
    "snmp":         ("snmp",         "SnmpModule",         "snmpUI"),
    "ves":          ("ves",          "VesModule",          "vesUI"),
    "webhook":      ("webhook",      "WebhookModule",      "webhookUI"),
    "protobuf":     ("protobuf",     "ProtobufModule",     "protobufUI"),
    "avro":         ("avro",         "AvroModule",         "sftpAvroUI"),
    "sftp":         ("sftp",         "SftpModule",         "sftpAvroUI"),
    "fm-console":   ("fm-console",   "FmConsoleModule",   "fmConsole"),
    "pm-dashboard": ("pm-dashboard", "PmDashboardModule", "pmDashboard"),
    "log-viewer":   ("log-viewer",   "LogViewerModule",   "logViewer"),
}


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
        meta["remote_url"]      = f"/mfe/{path_prefix}/assets/remoteEntry.js"
        meta["exposed"]         = f"./{module_name}"
        meta["federation_name"] = federation_name   # exact window.<key> Vite registers
        meta["health"]          = "healthy"
        plugins.append(meta)
    return {"plugins": plugins, "count": len(plugins)}
