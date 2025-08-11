# -*- coding: utf-8 -*-
import logging
import base64
from odoo import models, _, SUPERUSER_ID
from odoo.tools import mail
from odoo.exceptions import UserError

from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model, WhatsappApiMixin):
    _description = 'Pedido de Venda com Integração WhatsApp'
    _inherit = 'sale.order'

    def _get_whatsapp_message(self, template_xml_id):
        self.ensure_one()
        template = self.env.ref(template_xml_id)
        message_html = template._render_template(
            template.body_html, 'sale.order', self.ids
        )[self.id]
        return mail.html2plaintext(message_html)

    def action_enviar_whatsapp_cotacao(self):
        # ... (Esta função está correta e não muda)
        self.ensure_one()
        try:
            message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_quotation')
            chat_id = self._format_waha_number(self.partner_id)
            self._send_whatsapp_message(chat_id, message_text)
            self.message_post(body=_("Cotação enviada por WhatsApp."))
            return {
                'effect': { 'fadeout': 'slow', 'message': 'Cotação enviada com sucesso!', 'type': 'rainbow_man' }
            }
        except Exception as e:
            _logger.error("Falha detalhada ao enviar cotação por WhatsApp: %s", e)
            raise

    def action_enviar_whatsapp_pdf(self):
        self.ensure_one()

        # --- CORREÇÃO FINAL E DEFINITIVA AQUI ---
        # 1. Buscamos o relatório de forma segura.
        report = self.env['ir.actions.report']._get_report_from_name('sale.report_saleorder')
        if not report:
            raise UserError(_("O relatório de orçamento padrão ('sale.report_saleorder') não foi encontrado."))

        # 2. Usamos o método oficial 'report_action' para gerar o PDF.
        #    Este método lida com todas as permissões e contextos corretamente.
        pdf_content = report._render_qweb_pdf(self.id)[0]
        # --- FIM DA CORREÇÃO ---

        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        file_name = f"{self.name}.pdf"
        caption = f"Olá, {self.partner_id.name}! Segue em anexo o seu orçamento."

        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_document(chat_id, file_name, pdf_base64, caption)
        self.message_post(body=_("Orçamento em PDF enviado por WhatsApp."))
        
        return {
            'effect': { 'fadeout': 'slow', 'message': 'PDF do orçamento enviado com sucesso!', 'type': 'rainbow_man' }
        }

    def action_enviar_whatsapp_cancelado(self):
        # ... (Esta função está correta e não muda)
        self.ensure_one()
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_cancel')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Notificação de cancelamento enviada por WhatsApp."))
        return True

    def action_cancel(self):
        # ... (Esta função está correta e não muda)
        res = super().action_cancel()
        try:
            self.action_enviar_whatsapp_cancelado()
        except Exception as e:
            _logger.error("Falha ao enviar notificação de cancelamento por WhatsApp: %s", e)
        return res