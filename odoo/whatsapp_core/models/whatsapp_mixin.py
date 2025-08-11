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

    def _get_waha_url(self):
        return "http://waha:3000"

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
        waha_url = self._get_waha_url()
        api_key = "sua-chave-secreta-aqui"
        
        # 1. A URL volta a ser a genérica e correta
        api_url = f"{waha_url}/api/sendText"

        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": api_key,
        }
        
        # 2. Adicionamos a sessão DENTRO do payload
        payload = {
            "session": "default",
            "chatId": chat_id,
            "text": message_text,
        }

        # Mantemos nosso debug para confirmar
        _logger.info("----------- INICIANDO ENVIO DE MENSAGEM (DEBUG) -----------")
        _logger.info("URL da API: %s", api_url)
        _logger.info("Payload enviado: %s", payload)
        _logger.info("---------------------------------------------------------")

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            _logger.info("Mensagem enviada com sucesso. Resposta: %s", response.text)
            return True

        except requests.exceptions.RequestException as e:
            _logger.error("Erro ao conectar com a API do WhatsApp: %s", e)
            raise UserError(_("Falha ao enviar a mensagem via WhatsApp. Verifique a conexão com a API e tente novamente.\n\nDetalhe: %s", e))