# odoo/whatsapp_core/models/whatsapp_mixin.py
# -*- coding: utf-8 -*-
import requests
import re
import logging
from odoo import models, fields, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsappApiMixin(models.AbstractModel):
    _name = 'whatsapp.api.mixin'
    _description = 'Mixin para integração com API WhatsApp (WAHA)'

    def _get_waha_param(self, param_name):
        """Função auxiliar para buscar um parâmetro de configuração."""
        return self.env['ir.config_parameter'].sudo().get_param(param_name)

    def _format_waha_number(self, partner):
        # ... (esta função não muda)
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
        # --- MUDANÇA PRINCIPAL AQUI ---
        # Buscamos os dados dos parâmetros de sistema do Odoo
        waha_url = self._get_waha_param('whatsapp.api.url')
        api_key = self._get_waha_param('whatsapp.api.key')
        session = self._get_waha_param('whatsapp.api.session')

        if not waha_url or not api_key or not session:
            raise UserError(_("As configurações da API do WhatsApp não foram definidas. Vá em Configurações > Técnico > Parâmetros de Sistema."))

        api_url = f"{waha_url}/api/sendText"
        headers = { "Content-Type": "application/json", "X-Api-Key": api_key }
        payload = {
            "session": session,
            "chatId": chat_id,
            "text": message_text,
        }

        _logger.info("Enviando mensagem via WAHA. URL: %s, Payload: %s", api_url, payload)

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            _logger.info("Mensagem enviada com sucesso. Resposta: %s", response.text)
            return True
        except requests.exceptions.RequestException as e:
            _logger.error("Erro ao conectar com a API do WhatsApp: %s", e)
            raise UserError(_("Falha ao enviar a mensagem via WhatsApp. Verifique a conexão com a API e tente novamente.\n\nDetalhe: %s", e))
        
    def _send_whatsapp_document(self, chat_id, file_name, base64_data, caption=''):
        """Envia um documento (PDF) codificado em Base64."""
        waha_url = self._get_waha_param('whatsapp.api.url')
        api_key = self._get_waha_param('whatsapp.api.key')
        session = self._get_waha_param('whatsapp.api.session')

        if not waha_url or not api_key or not session:
            raise UserError(_("As configurações da API do WhatsApp não foram definidas."))

        # A URL da API para enviar arquivos é diferente
        api_url = f"{waha_url}/api/sendDocument"
        headers = { "Content-Type": "application/json", "X-Api-Key": api_key }
        payload = {
            "session": session,
            "chatId": chat_id,
            "file": {
                "mimetype": "application/pdf",
                "filename": file_name,
                "data": base64_data
            },
            "caption": caption # Legenda opcional para o arquivo
        }

        _logger.info("Enviando DOCUMENTO via WAHA. URL: %s", api_url)

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=20) # Aumentamos o timeout para arquivos
            response.raise_for_status()
            _logger.info("Documento enviado com sucesso. Resposta: %s", response.text)
            return True
        except requests.exceptions.RequestException as e:
            _logger.error("Erro ao enviar documento via WhatsApp: %s", e)
            raise UserError(_("Falha ao enviar o documento via WhatsApp.\n\nDetalhe: %s", e))