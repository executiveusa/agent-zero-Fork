from python.helpers.api import ApiHandler, Request, Response


class VoiceCommandRoute(ApiHandler):
    """API endpoint: POST /voice_command_route
    Routes a voice/text utterance through the SYNTHIA command registry.
    """

    async def process(self, input: dict, request: Request) -> dict | Response:
        from python.helpers.voice_command_router import VoiceCommandRouter

        utterance = input.get("utterance", "").strip()
        if not utterance:
            return {"error": "No utterance provided", "matched_command": None}

        router = VoiceCommandRouter()
        match = router.match(utterance)

        if match is None:
            return {
                "matched_command": None,
                "utterance": utterance,
                "message": "No command matched. Treating as general conversation.",
            }

        return {
            "matched_command": match.command.id,
            "confidence": round(match.confidence, 2),
            "tool_name": match.command.tool_name,
            "tool_args_template": match.command.tool_args_template,
            "missing_slots": match.missing_slots,
            "category": match.command.category.value,
            "needs_confirmation": match.command.confirm,
            "admin_only": match.command.admin_only,
            "utterance": utterance,
        }
