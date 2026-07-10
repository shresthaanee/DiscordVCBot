from aiohttp import web
from light import light_on, light_off
from voice import find_member_in_voice


def check_auth(request, secret):
    return request.headers.get("X-Secret") == secret


def setup(bot, secret: str, port: int):

    async def handle_mute(request):
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        data    = await request.json()
        user_id = int(data.get("user_id", 0))
        mute    = data.get("mute", True)

        # Debug — print all voice members the bot can currently see
        for guild in bot.guilds:
            for vc in guild.voice_channels:
                ids = [m.id for m in vc.members]
                print(f"🔍 {vc.name}: {ids}")
        print(f"🔍 Looking for user_id: {user_id}")

        member  = find_member_in_voice(bot, user_id)
        if member is None:
            return web.Response(status=404, text="User not in voice")
        await member.edit(mute=mute)
        action = "muted" if mute else "unmuted"
        print(f"🔇 {member.display_name} {action} via widget")
        return web.Response(text=f"{member.display_name} {action}")

    async def handle_deafen(request):
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        data    = await request.json()
        user_id = int(data.get("user_id", 0))
        deafen  = data.get("deafen", True)
        member  = find_member_in_voice(bot, user_id)
        if member is None:
            return web.Response(status=404, text="User not in voice")
        await member.edit(deafen=deafen)
        action = "deafened" if deafen else "undeafened"
        print(f"🔕 {member.display_name} {action} via widget")
        return web.Response(text=f"{member.display_name} {action}")

    async def handle_light(request):
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        data   = await request.json()
        action = data.get("action", "on")
        if action == "on":
            await light_on()
        else:
            await light_off()
        return web.Response(text=f"Light {action}")

    async def handle_vcwho(request):
        if not check_auth(request, secret):
            return web.Response(status=401, text="Unauthorized")
        result = {}
        for guild in bot.guilds:
            for vc in guild.voice_channels:
                members = [
                    {"name": m.display_name, "user_id": str(m.id)}
                    for m in vc.members if not m.bot
                ]
                if members:
                    result[vc.name] = members
        if not result:
            return web.Response(text="Nobody in voice")
        return web.json_response(result)

    async def start():
        app = web.Application()
        app.router.add_post("/mute",   handle_mute)
        app.router.add_post("/deafen", handle_deafen)
        app.router.add_post("/light",  handle_light)
        app.router.add_get("/vcwho",   handle_vcwho)
        runner = web.AppRunner(app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", port).start()
        print(f"🌐 Web API running on port {port}")

    return start
