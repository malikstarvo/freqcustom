from pathlib import Path

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.responses import FileResponse


router_ui = APIRouter(include_in_schema=False, tags=["Web UI"])


def _ui_installed_dir() -> Path:
    from freqtrade.rpc.api_server.webserver import ApiServer

    config = ApiServer._config
    if config and config.get("user_data_dir"):
        user_ui = Path(config["user_data_dir"]) / "ui"
        if user_ui.is_dir():
            return user_ui
    return Path(__file__).parent / "ui/installed"


@router_ui.get("/favicon.ico")
async def favicon():
    return FileResponse(str(Path(__file__).parent / "ui/favicon.ico"))


@router_ui.get("/fallback_file.html")
async def fallback():
    return FileResponse(str(Path(__file__).parent / "ui/fallback_file.html"))


@router_ui.get("/ui_version")
async def ui_version():
    from freqtrade.commands.deploy_ui import read_ui_version

    version = read_ui_version(_ui_installed_dir())

    return {
        "version": version if version else "not_installed",
    }


@router_ui.get("/{rest_of_path:path}")
async def index_html(rest_of_path: str):
    if rest_of_path.startswith("api") or rest_of_path.startswith(".") or rest_of_path == "metrics":
        raise HTTPException(status_code=404, detail="Not Found")
    uibase = _ui_installed_dir().resolve()
    filename = (uibase / rest_of_path).resolve()
    media_type: str | None = None
    if filename.suffix == ".js":
        media_type = "application/javascript"
    if filename.is_file() and filename.is_relative_to(uibase):
        return FileResponse(str(filename), media_type=media_type)

    index_file = uibase / "index.html"
    if not index_file.is_file():
        return FileResponse(str(Path(__file__).parent / "ui/fallback_file.html"))
    return FileResponse(str(index_file))
