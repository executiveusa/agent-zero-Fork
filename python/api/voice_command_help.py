from python.helpers.api import ApiHandler, Request, Response


class VoiceCommandHelp(ApiHandler):
    """API endpoint: POST /voice_command_help
    Returns the full command registry for the SYNTHIA help grid.
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        from python.helpers.voice_command_router import VoiceCommandRouter

        router = VoiceCommandRouter()
        category_filter = input.get("category", None)

        commands = []
        for cmd in router.registry:
            if category_filter and cmd.category.value != category_filter:
                continue
            commands.append({
                "id": cmd.id,
                "category": cmd.category.value,
                "triggers": cmd.triggers[:4],
                "tool_name": cmd.tool_name,
                "confirm": cmd.confirm,
                "admin_only": cmd.admin_only,
            })

        return {"commands": commands, "total": len(commands)}
