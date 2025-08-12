# odoo/whatsapp_core/models/whatsapp_mixin.py
import requests
import re
import logging
from odoo import models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsappApiMixin(models.AbstractModel):
    _name = 'whatsapp.api.mixin'
    _description = 'Mixin para integração com API WhatsApp (WAHA)'

    def _get_waha_param(self, param_name):
        return self.env['ir.config_parameter'].sudo().get_param(param_name)

    def _format_waha_number(self, partner):
        if not partner.phone and not partner.mobile:
            raise UserError(_("O cliente '%s' não possui um número de telefone ou celular cadastrado.", partner.name))
        number = partner.mobile or partner.phone
        clean_number = re.sub(r'\D', '', number)
        if not clean_number.startswith('55'):
            if 10 <= len(clean_number) <= 11:
                clean_number = f"55{clean_number}"
            else:
                raise UserError(_("O número de telefone '%s' não parece ser um número brasileiro válido.", number))
        return f"{clean_number}@c.us"

    def _send_whatsapp_message(self, chat_id, message_text):
        waha_url = self._get_waha_param('whatsapp.api.url')
        api_key = self._get_waha_param('whatsapp.api.key')
        session = self._get_waha_param('whatsapp.api.session')
        if not waha_url or not api_key or not session:
            raise UserError(_("As configurações da API do WhatsApp não foram definidas."))
        api_url = f"{waha_url}/api/sendText"
        headers = { "Content-Type": "application/json", "X-Api-Key": api_key }
        payload = {"session": session, "chatId": chat_id, "text": message_text}
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise UserError(_("Falha ao enviar a mensagem via WhatsApp.\n\nDetalhe: %s", e))
        
    def _send_whatsapp_document(self, chat_id, file_name, base64_data, mimetype, caption=''):
        waha_url = self._get_waha_param('whatsapp.api.url')
        api_key = self._get_waha_param('whatsapp.api.key')
        session = self._get_waha_param('whatsapp.api.session')
        if not waha_url or not api_key or not session:
            raise UserError(_("As configurações da API do WhatsApp não foram definidas."))
        
        api_url = f"{waha_url}/api/sendFile"
        
        headers = { "Content-Type": "application/json", "X-Api-Key": api_key }
        
        payload = {
            "session": session,
            "chatId": chat_id,
            "file": {
                "mimetype": mimetype,
                "filename": file_name,
                "data": base64_data,
            },
            "caption": caption
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            raise UserError(_("Falha ao enviar o documento via WhatsApp.\n\nDetalhe: %s", e))