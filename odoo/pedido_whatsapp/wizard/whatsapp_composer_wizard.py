# -*- coding: utf-8 -*-
import base64
import requests
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsappComposerWizard(models.TransientModel):
    # Herda todo o comportamento do wizard de e-mail do Odoo
    _inherit = 'mail.compose.message'

    # Adicionamos um campo para mostrar o número do WhatsApp
    whatsapp_number = fields.Char(string="Nº WhatsApp")

    def _send_document_to_workwise(self, order_name, pdf_bytes, file_name):
        """
        Função de envio para a API da WorkWise com dados hardcoded.
        """
        workwise_url = "https://hmlapi.workwise.com.br/upload"
        workwise_token = "MEU_TOKEN_SUPER_SEGURO"  # Lembre-se de usar o token real

        headers = {'Authorization': f'Bearer {workwise_token}'}
        files = {'file': (file_name, pdf_bytes, 'application/pdf')}
        data = {'order_name': order_name}

        _logger.info("Enviando arquivo '%s' para a API WorkWise.", file_name)
        try:
            response = requests.post(workwise_url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            _logger.info("Resposta da API WorkWise: SUCESSO")
            return True
        except requests.exceptions.RequestException as e:
            raise UserError(_("Falha ao enviar o PDF para a API Externa.\n\nDetalhe: %s") % str(e))

    def _send_whatsapp_message(self, chat_id, message_text):
        """
        Função de envio para a API do WAHA.
        """
        config_param = self.env['ir.config_parameter'].sudo()
        waha_url = config_param.get_param('whatsapp.api.url')
        api_key = config_param.get_param('whatsapp.api.key')
        session = config_param.get_param('whatsapp.api.session')

        if not waha_url or not api_key or not session:
            raise UserError(_("As configurações da API do WhatsApp (WAHA) não foram definidas."))

        api_url = f"{waha_url}/api/sendText"
        headers = { "Content-Type": "application/json", "X-Api-Key": api_key }
        payload = {"session": session, "chatId": chat_id, "text": message_text}
        
        _logger.info("Enviando mensagem de texto para a API WAHA.")
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            _logger.info("Resposta da API WAHA: SUCESSO")
            return True
        except requests.exceptions.RequestException as e:
            raise UserError(_("Falha ao enviar a mensagem via WhatsApp (WAHA).\n\nDetalhe: %s") % e)

    def action_send_whatsapp(self):
        """
        Esta é a nova função que nosso botão 'Enviar via WhatsApp' vai chamar.
        """
        self.ensure_one()
        order = self.env['sale.order'].browse(self.env.context.get('active_id'))

        # 1. Enviar a mensagem de texto via WAHA
        self._send_whatsapp_message(self.whatsapp_number, self.body)

        # 2. Enviar o PDF para a API WorkWise
        if self.attachment_ids:
            attachment = self.attachment_ids[0]
            pdf_bytes = base64.b64decode(attachment.datas)
            self._send_document_to_workwise(order.name, pdf_bytes, attachment.name)

        order.message_post(body=_("Mensagem e PDF enviados via Composer do WhatsApp."))
        
        return {
            'effect': { 'fadeout': 'slow', 'message': 'WhatsApp e PDF enviados!', 'type': 'rainbow_man' }
        }