# -*- coding: utf-8 -*-
import base64
import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class WhatsappComposerWizard(models.TransientModel):
    _name = 'whatsapp.composer.wizard'
    _description = 'Assistente para Envio de Pedidos por WhatsApp'

    whatsapp_number = fields.Char(string="Número do WhatsApp", required=True)
    message_body = fields.Text(string="Mensagem", required=True)
    attachment_ids = fields.Many2many('ir.attachment', string="Anexos")

    def action_send_message(self):
        self.ensure_one()
        sale_order_id = self.env.context.get('active_id')
        order = self.env['sale.order'].browse(sale_order_id)

        if not self.attachment_ids:
            raise UserError(_("É necessário ter pelo menos um anexo para enviar."))

        pdf_attachment = self.attachment_ids[0]
        pdf_content_b64 = pdf_attachment.datas.decode('utf-8')
        pdf_content_bytes = base64.b64decode(pdf_content_b64)
        file_name = pdf_attachment.name

        # Variáveis para controlar o sucesso de cada operação
        waha_success = False
        workwise_success = False
        error_logs = []

        # --- 1. Tenta enviar para o cliente via WAHA ---
        try:
            order._send_whatsapp_document(
                chat_id=self.whatsapp_number,
                file_name=file_name,
                base64_data=pdf_content_b64,
                mimetype='application/pdf',
                caption=self.message_body
            )
            order.message_post(body=_("✅ Documento enviado com sucesso para o cliente via WhatsApp."))
            waha_success = True
        except Exception as e:
            error_message = _("❌ Falha ao enviar a mensagem para o cliente via WAHA: %s") % e
            error_logs.append(error_message)
            order.message_post(body=error_message)

        # --- 2. Tenta enviar para a API Workwise ---
        try:
            workwise_url = self.env['ir.config_parameter'].sudo().get_param('workwise.api.url')
            workwise_token = self.env['ir.config_parameter'].sudo().get_param('workwise.api.token')

            if not workwise_url or not workwise_token:
                raise UserError(_("As configurações da API Workwise (URL ou Token) não foram definidas."))

            headers = {'Authorization': f'Bearer {workwise_token}'}
            files = {'file': (file_name, pdf_content_bytes, 'application/pdf')}
            payload = {'order_name': order.name}

            response = requests.post(workwise_url, headers=headers, files=files, data=payload, timeout=20)
            response.raise_for_status()

            order.message_post(body=_("✅ Documento enviado com sucesso para a API Workwise."))
            workwise_success = True
        except Exception as e:
            error_message = _("❌ Falha ao enviar para a API Workwise: %s") % e
            error_logs.append(error_message)
            order.message_post(body=error_message)

        # --- 3. Feedback final para o usuário ---
        if not error_logs:
            # Sucesso total!
            return {
                'effect': { 'fadeout': 'slow', 'message': 'Tudo certo! Mensagem e documento enviados com sucesso!', 'type': 'rainbow_man' }
            }
        else:
            # Falha parcial ou total, exibe um erro claro
            final_error_message = "\n\n".join(error_logs)
            raise UserError(_("A operação foi concluída com os seguintes problemas:\n\n%s") % final_error_message)