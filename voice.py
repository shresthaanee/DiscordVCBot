import time
from collections import defaultdict
from discord.ext import tasks
from light import light_on, light_off

# user_id → timestamp when they joined current session
join_times = {}

# user_id → total seconds spent in voice today
# { user_id: {"name": str, "total": float} }
daily_totals = defaultdict(lambda: {"name": "", "total": 0.0})


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, rem  = divmod(seconds, 3600)
    m, s    = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def anyone_in_voice(bot):
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            if any(not m.bot for m in vc.members):
                return True
    return False


def find_member_in_voice(bot, user_id: int):
    for guild in bot.guilds:
        for vc in guild.voice_channels:
            for member in vc.members:
                if member.id == user_id:
                    return member
    return None


def get_session_duration(user_id: int) -> float | None:
    """Return how long (seconds) a user has been in voice this session."""
    if user_id not in join_times:
        return None
    return time.time() - join_times[user_id]


def _record_join(member):
    join_times[member.id] = time.time()
    daily_totals[member.id]["name"] = member.display_name


def _record_leave(member) -> float:
    """Remove join record, accumulate to daily total, return session seconds."""
    if member.id not in join_times:
        return 0.0
    duration = time.time() - join_times.pop(member.id)
    daily_totals[member.id]["name"]  = member.display_name
    daily_totals[member.id]["total"] += duration
    return duration


def setup(bot, log_channel_id: int):

    @tasks.loop(time=__import__("datetime").time(hour=18, minute=15))
    async def post_daily_summary():
        log_channel = bot.get_channel(log_channel_id)
        if log_channel is None:
            return

        # Flush anyone still in voice into the totals
        for uid, joined_at in list(join_times.items()):
            duration = time.time() - joined_at
            daily_totals[uid]["total"] += duration
            join_times[uid] = time.time()  # reset so they keep accumulating tomorrow

        if not daily_totals:
            await log_channel.send("📋 **Daily Summary** — Nobody was in voice today.")
            return

        lines = ["📋 **Daily Voice Summary**", "─" * 30]
        sorted_users = sorted(daily_totals.items(), key=lambda x: x[1]["total"], reverse=True)
        for uid, data in sorted_users:
            if data["total"] > 0:
                lines.append(f"👤 **{data['name']}** — {format_duration(data['total'])}")

        lines.append("─" * 30)
        total_all = sum(d["total"] for d in daily_totals.values())
        lines.append(f"⏱️ Total voice time today: **{format_duration(total_all)}**")

        await log_channel.send("\n".join(lines))

        # Reset for next day
        daily_totals.clear()

    @bot.event
    async def on_ready():
        post_daily_summary.start()

    @bot.event
    async def on_voice_state_update(member, before, after):
        if member.bot:
            return

        log_channel = bot.get_channel(log_channel_id)
        if log_channel is None:
            return

        joined   = before.channel is None and after.channel is not None
        left     = before.channel is not None and after.channel is None
        switched = (
            before.channel is not None
            and after.channel is not None
            and before.channel != after.channel
        )

        if joined:
            _record_join(member)
            await log_channel.send(
                f"👋 Welcome **{member.display_name}** joined **{after.channel.name}**!"
            )
            await light_on()

        elif left:
            duration = _record_leave(member)
            dur_str  = f" · ⏱️ {format_duration(duration)}" if duration > 0 else ""
            await log_channel.send(
                f"👋 Bye **{member.display_name}** left **{before.channel.name}**!{dur_str}"
            )
            if not anyone_in_voice(bot):
                await light_off()
                await log_channel.send("💡 No one left in voice — light turned off.")

        elif switched:
            await log_channel.send(
                f"🔀 **{member.display_name}** moved from **{before.channel.name}** to **{after.channel.name}**."
            )
