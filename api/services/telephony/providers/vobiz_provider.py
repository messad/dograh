import os
import uuid
import json
from loguru import logger
from livekit import api
from api.services.telephony.providers.base_provider import BaseTelephonyProvider

# --- AYARLAR ---
# Senin oluşturduğun Verimor Trunk ID
SIP_TRUNK_ID = "ST_Dzv3kw6XKsV5"

# Ortam değişkenleri (Coolify'dan gelecek)
LIVEKIT_URL = os.getenv("SERVICE_FQDN_LIVEKIT", "https://live.davetly.net.tr")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

class VobizProvider(BaseTelephonyProvider):
    def __init__(self, **kwargs):
        logger.info(f"VERIMOR-BRIDGE: Baslatiliyor... Trunk: {SIP_TRUNK_ID}")
        try:
            self.lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
            logger.success("VERIMOR-BRIDGE: LiveKit API baglantisi hazir.")
        except Exception as e:
            logger.error(f"VERIMOR-BRIDGE: LiveKit API hatasi: {e}")

    # Sistem çağrı başlatırken bu fonksiyonu kullanır
    async def initiate_call(self, to_phone: str, from_phone: str = None, workflow_run_id: str = None, **kwargs):
        return await self._trigger_verimor(to_phone, workflow_run_id)

    # Yedek olarak bunu da ekliyoruz (bazı versiyonlar bunu çağırır)
    async def create_outbound_call(self, to_phone: str, from_phone: str = None, workflow_run_id: str = None, **kwargs):
        return await self._trigger_verimor(to_phone, workflow_run_id)

    async def _trigger_verimor(self, to_phone, workflow_run_id):
        try:
            # Numara Formatlama (+90 zorunluluğu)
            clean_phone = str(to_phone).strip()
            if not clean_phone.startswith("+"):
                if clean_phone.startswith("0"):
                    clean_phone = "+9" + clean_phone # 05xx -> +905xx
                elif clean_phone.startswith("90"):
                    clean_phone = "+" + clean_phone  # 905xx -> +905xx
                else:
                    clean_phone = "+90" + clean_phone # 5xx -> +905xx
            
            room_name = workflow_run_id if workflow_run_id else f"call_{str(uuid.uuid4())}"
            
            logger.info(f"VERIMOR-BRIDGE: Arama istegi geldi -> {clean_phone}")

            # LiveKit SIP üzerinden Verimor'u tetikle
            participant = await self.lkapi.sip.create_sip_participant(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=clean_phone,
                room_name=room_name,
                participant_identity=f"phone_{clean_phone}",
                participant_name="Musteri",
                play_ringtone=False
            )
            
            logger.success(f"VERIMOR-BRIDGE: Verimor ariyor! Call ID: {participant.sip_call_id}")
            
            # Dograh'a Vobiz formatında sahte başarılı yanıt dön
            return {
                "id": participant.sip_call_id,
                "status": "queued",
                "provider": "vobiz",
                "details": {"room_name": room_name}
            }

        except Exception as e:
            logger.error(f"VERIMOR-BRIDGE HATASI: {str(e)}")
            raise e

    async def validate_request(self, request):
        return True

    async def handle_webhook(self, payload):
        return {"status": "ignored"}
