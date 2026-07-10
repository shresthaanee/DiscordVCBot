# Light control via Tuya Cloud API (Nedis SmartLife)
# Commented out — uncomment when Tuya credentials are ready

# import tinytuya
# import os
# import asyncio
#
# DEVICE_ID     = os.getenv("TUYA_DEVICE_ID")
# REGION        = os.getenv("TUYA_REGION", "eu")
# ACCESS_ID     = os.getenv("TUYA_ACCESS_ID")
# ACCESS_SECRET = os.getenv("TUYA_ACCESS_SECRET")
#
#
# def _get_cloud():
#     return tinytuya.Cloud(
#         apiRegion=REGION,
#         apiKey=ACCESS_ID,
#         apiSecret=ACCESS_SECRET,
#         apiDeviceID=DEVICE_ID,
#     )
#
#
# def _light_on():
#     try:
#         _get_cloud().sendcommand(DEVICE_ID, [{"code": "switch_led", "value": True}])
#         print("💡 Light ON")
#     except Exception as e:
#         print(f"⚠️  Light ON failed: {e}")
#
#
# def _light_off():
#     try:
#         _get_cloud().sendcommand(DEVICE_ID, [{"code": "switch_led", "value": False}])
#         print("🌑 Light OFF")
#     except Exception as e:
#         print(f"⚠️  Light OFF failed: {e}")
#
#
# async def light_on():
#     await asyncio.get_event_loop().run_in_executor(None, _light_on)
#
#
# async def light_off():
#     await asyncio.get_event_loop().run_in_executor(None, _light_off)


# ── Stubs so the rest of the bot imports cleanly ──────────────────────────────

async def light_on():
    print("💡 Light ON (disabled — Tuya not configured)")

async def light_off():
    print("🌑 Light OFF (disabled — Tuya not configured)")
