# -*- coding: utf-8 -*-
import base64
import requests
import logging
from odoo import models, fields, _, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class SaleOrderSendPdfWizard(models.TransientModel):
    _name = 'sale.order.send_pdf.wizard'
    _description = 'Wizard para Anexar e Enviar PDF da Cotação'

    attachment = fields.Binary(string="Anexar PDF", required=True)
    file_name = fields.Char(string="Nome do Arquivo", required=True)

    def _send_document_to_workwise(self, order, file_name, pdf_bytes):
        """
        Função de envio para a API da WorkWise com dados hardcoded.
        """
        workwise_url = "https://hmlapi.workwise.com.br/upload"
        workwise_token = "MEU_TOKEN_SUPER_SEGURO"  # Lembre-se de usar o token real

        headers = {'Authorization': f'Bearer {workwise_token}'}
        files = {'file': (file_name, pdf_bytes, 'application/pdf')}
        data = {'order_name': order.name}

        _logger.info("Enviando arquivo '%s' para a API WorkWise.", file_name)
        try:
            response = requests.post(workwise_url, headers=headers, files=files, data=data, timeout=30)
            response.raise_for_status()
            _logger.info("Resposta da API: SUCESSO")
            return True
        except requests.exceptions.RequestException as e:
            raise UserError(_("Falha ao enviar o documento para a API Externa.\n\nDetalhe: %s") % str(e))

    def action_send_file(self):
        self.ensure_one()
        # Pega a cotação que estava aberta na tela
        order = self.env['sale.order'].browse(self.env.context.get('active_id'))
        # Converte o anexo para bytes
        pdf_bytes = base64.b64decode(self.attachment)

        # Chama a função de envio
        self._send_document_to_workwise(order, self.file_name, pdf_bytes)

        # Adiciona uma mensagem no histórico do pedido
        order.message_post(body=_("PDF '%s' enviado para a API Externa via anexo.", self.file_name))
        
        # Retorna a mensagem de sucesso
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'PDF enviado com sucesso!',
                'type': 'rainbow_man',
            }
        }