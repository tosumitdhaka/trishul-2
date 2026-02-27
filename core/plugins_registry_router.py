"""GET /api/v1/plugins/registry — returns all loaded plugin metadata + MFE remote URLs."""
from fastapi import APIRouter, Request

router = APIRouter(tags=["plugins"])


@router.get("/api/v1/plugins/registry")
async def get_plugin_registry(request: Request):
    registry = request.app.state.plugin_registry
    plugins  = []
    for name, plugin in registry.plugins.items():
        meta = plugin.get_metadata()
        # MFE remote URL convention: http://{name}-ui/assets/remoteEntry.js
        # (resolved by Traefik on the internal Docker network)
        meta["remote_url"] = f"/mfe/{name}/assets/remoteEntry.js"
        meta["exposed"]    = f"./{name.capitalize()}Module"
        meta["health"]     = "healthy"
        plugins.append(meta)
    return {"plugins": plugins, "count": len(plugins)}
