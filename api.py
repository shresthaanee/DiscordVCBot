from aiohttp import web
from light import light_on, light_off
from voice import find_member_in_voice, get_session_duration, format_duration


def check_auth(request, secret):
    return request.headers.get("X-Secret") == secret


def parse_user_id(data):
    try:
        return int(data.get("user_id", 0))
    except (ValueError, TypeError):
        return 0


def get_member_status(bot, user_id: int):
    """Return member and their current voice status."""
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.id == user_id:
                    vs = member.voice
                    secs = get_session_duration(member.id)
                    return member, {
                        "name":             member.display_name,
                        "user_id":          str(member.id),
                        "channel":          vc.name,
                        "muted":            vs.mute,
                        "deafened":         vs.deaf,
                        "self_muted":       vs.self_mute,
                        "camera_on":        vs.self_video,
                        "session_duration": format_duration(secs) if secs else "unknown",
                        "in_voice":         True,
                    }
    return None, {"in_voice": False}


def setup(bot, secret: str, port: int):

    # ── Status ────────────────────────────────────────────────────────────────

    async def handle_status(request):
        """GET /status?user_id=123  — returns voice status of a user."""
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        try:
            user_id = int(request.rel_url.query.get("user_id", 0))
        except ValueError:
            return web.Response(status=400, text="Invalid user_id")
        if user_id == 0:
            return web.Response(status=400, text="Missing user_id")
        _, status = get_member_status(bot, user_id)
        return web.json_response(status)

    async def handle_vcwho(request):
        """GET /vcwho — returns all users in voice with their status."""
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        result = {}
        for guild in bot.guilds:
            for vc in guild.voice_channels:
                members = []
                for m in vc.members:
                    if m.bot:
                        continue
                    vs   = m.voice
                    secs = get_session_duration(m.id)
                    members.append({
                        "name":             m.display_name,
                        "user_id":          str(m.id),
                        "muted":            vs.mute,
                        "deafened":         vs.deaf,
                        "camera_on":        vs.self_video,
                        "session_duration": format_duration(secs) if secs else "unknown",
                    })
                if members:
                    result[vc.name] = members
        if not result:
            return web.json_response({"channels": {}, "total": 0})
        return web.json_response({"channels": result, "total": sum(len(v) for v in result.values())})

    # ── Mute (set or toggle) ──────────────────────────────────────────────────

    async def handle_mute(request):
        """POST /mute  body: {user_id, mute: true/false} or {user_id, toggle: true}"""
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid JSON body")

        user_id = parse_user_id(data)
        if user_id == 0:
            return web.Response(status=400, text="Missing or invalid user_id")

        member, status = get_member_status(bot, user_id)
        if member is None:
            return web.Response(status=404, text="User not in voice")

        if data.get("toggle"):
            mute = not status["muted"]
        else:
            mute = data.get("mute", True)

        await member.edit(mute=mute)
        action = "muted" if mute else "unmuted"
        print(f"🔇 {member.display_name} {action} via widget")
        return web.json_response({"user": member.display_name, "muted": mute})

    # ── Deafen (set or toggle) ────────────────────────────────────────────────

    async def handle_deafen(request):
        """POST /deafen  body: {user_id, deafen: true/false} or {user_id, toggle: true}"""
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid JSON body")

        user_id = parse_user_id(data)
        if user_id == 0:
            return web.Response(status=400, text="Missing or invalid user_id")

        member, status = get_member_status(bot, user_id)
        if member is None:
            return web.Response(status=404, text="User not in voice")

        if data.get("toggle"):
            deafen = not status["deafened"]
        else:
            deafen = data.get("deafen", True)

        await member.edit(deafen=deafen)
        action = "deafened" if deafen else "undeafened"
        print(f"🔕 {member.display_name} {action} via widget")
        return web.json_response({"user": member.display_name, "deafened": deafen})

    # ── Combined action endpoint ──────────────────────────────────────────────

    async def handle_nugahlive_action(request):
        """
        POST /nugahlive/action
        Body (all fields optional — only include what you want to change):
        {
            "user_id": "618...",

            "mute":         true/false,   # explicit mute/unmute
            "mute_toggle":  true,         # flip current mute state

            "deafen":       true/false,   # explicit deafen/undeafen
            "deafen_toggle": true         # flip current deafen state
        }
        You can combine any of these in one call.
        """
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid JSON body")

        user_id = parse_user_id(data)
        if user_id == 0:
            return web.Response(status=400, text="Missing or invalid user_id")

        member, status = get_member_status(bot, user_id)
        if member is None:
            return web.Response(status=404, text="User not in voice")

        result = {"user": member.display_name}

        # Resolve mute
        new_mute = None
        if data.get("mute_toggle"):
            new_mute = not status["muted"]
        elif "mute" in data:
            new_mute = bool(data["mute"])

        # Resolve deafen
        new_deafen = None
        if data.get("deafen_toggle"):
            new_deafen = not status["deafened"]
        elif "deafen" in data:
            new_deafen = bool(data["deafen"])

        if new_mute is None and new_deafen is None:
            return web.Response(status=400, text="No action specified. Use mute, mute_toggle, deafen, or deafen_toggle.")

        # Apply — build kwargs so we only send what changed
        kwargs = {}
        if new_mute   is not None: kwargs["mute"]   = new_mute
        if new_deafen is not None: kwargs["deafen"]  = new_deafen
        await member.edit(**kwargs)

        if new_mute   is not None: result["muted"]   = new_mute
        if new_deafen is not None: result["deafened"] = new_deafen

        print(f"⚡ /nugahlive/action → {result}")
        return web.json_response(result)

    # ── Disconnect ───────────────────────────────────────────────────────────

    async def handle_disconnect(request):
        """POST /nugahlive/disconnect  body: {user_id}"""
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid JSON body")

        user_id = parse_user_id(data)
        if user_id == 0:
            return web.Response(status=400, text="Missing or invalid user_id")

        member, status = get_member_status(bot, user_id)
        if member is None:
            return web.Response(status=404, text="User not in voice")

        channel = status["channel"]
        await member.move_to(None)
        print(f"👢 {member.display_name} disconnected from {channel} via widget")
        return web.json_response({"user": member.display_name, "disconnected_from": channel})

    # ── Light ─────────────────────────────────────────────────────────────────

    async def handle_light(request):
        """POST /light  body: {action: "on"/"off"}"""
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        try:
            data = await request.json()
        except Exception:
            return web.Response(status=400, text="Invalid JSON body")
        action = data.get("action", "on")
        if action == "on":
            await light_on()
        else:
            await light_off()
        return web.json_response({"light": action})

    # ── Server ────────────────────────────────────────────────────────────────

    async def handle_health(request):
        """GET /health — Koyeb health check, no auth needed."""
        return web.Response(text="ok")

    async def start():
        app = web.Application()
        app.router.add_get("/health",  handle_health)
        app.router.add_get("/status",  handle_status)
        app.router.add_get("/vcwho",   handle_vcwho)
        app.router.add_post("/mute",                 handle_mute)
        app.router.add_post("/deafen",               handle_deafen)
        app.router.add_post("/nugahlive/action",     handle_nugahlive_action)
        app.router.add_post("/nugahlive/disconnect", handle_disconnect)
        app.router.add_post("/light",                handle_light)
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        print(f"🌐 Web API running on port {port}")

    return start
