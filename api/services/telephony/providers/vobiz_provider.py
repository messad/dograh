import os
import json
import uuid
from loguru import logger
from livekit import api
from api.services.telephony.providers.base_provider import BaseTelephonyProvider

# --- AYARLAR ---
# Senin sisteminde LiveKit ortam değişkenleri tanımlı olduğu için doğrudan çekiyoruz
LIVEKIT_URL = os.getenv("SERVICE_FQDN_LIVEKIT")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")

# Senin SIP Trunk ID'n
SIP_TRUNK_ID = "ST_Dzv3kw6XKsV5"

class VobizProvider(BaseTelephonyProvider):
    def __init__(self):
        self.lkapi = api.LiveKitAPI(LIVEKIT_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET)
        logger.info(f"VobizProvider (Verimor Modu) başlatıldı. Trunk: {SIP_TRUNK_ID}")

    async def create_outbound_call(self, to_phone: str, from_phone: str = None, workflow_run_id: str = None):
        try:
            # Numara temizliği (+90 formatı)
            clean_phone = to_phone.strip()
            if not clean_phone.startswith("+"):
                if clean_phone.startswith("0"):
                    clean_phone = "+9" + clean_phone
                elif clean_phone.startswith("90"):
                    clean_phone = "+" + clean_phone
                else:
                    clean_phone = "+90" + clean_phone
            
            room_name = workflow_run_id if workflow_run_id else f"call_{str(uuid.uuid4())}"
            
            logger.info(f"Verimor Araması Tetikleniyor -> Hedef: {clean_phone}")

            # LiveKit SIP araması başlat
            participant = await self.lkapi.sip.create_sip_participant(
                sip_trunk_id=SIP_TRUNK_ID,
                sip_call_to=clean_phone,
                room_name=room_name,
                participant_identity=f"phone_{clean_phone}",
                participant_name="Musteri"
            )
            
            logger.success(f"Arama Başladı! SIP Call ID: {participant.sip_call_id}")
            
            return {
                "id": participant.sip_call_id,
                "status": "queued",
                "provider": "vobiz",
                "details": {"room_name": room_name}
            }

        except Exception as e:
            logger.error(f"Arama hatası: {e}")
            raise e

    async def validate_request(self, request):
        return True

    async def handle_webhook(self, payload):
        return {"status": "ignored"}
