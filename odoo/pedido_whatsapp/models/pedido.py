# odoo/pedido_whatsapp/models/pedido.py
import logging
import base64
from odoo import models, _, SUPERUSER_ID
from odoo.tools import mail
from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model, WhatsappApiMixin):
    _inherit = 'sale.order'
    _description = 'Pedido de Venda com Integração WhatsApp'

    def action_open_whatsapp_composer(self):
        """
        Prepara e abre o wizard 'composer' com o contexto correto.
        """
        self.ensure_one()
        
        report = self.env.ref('sale.action_report_saleorder').with_user(SUPERUSER_ID)
        pdf_bytes, content_type = report._render_qweb_pdf([self.id])
        pdf_base64 = base64.b64encode(pdf_bytes)

        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}.pdf",
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'mail.compose.message',
            'res_id': 0,
            'mimetype': 'application/pdf',
        })

        if self.state in ['draft', 'sent']:
            template_xml_id = 'pedido_whatsapp.mail_template_sale_quotation'
        else:
            template_xml_id = 'pedido_whatsapp.mail_template_sale_confirmation'
        
        template = self.env.ref(template_xml_id)
        
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': False,
            'default_template_id': None,
            'default_composition_mode': 'comment',
            'default_subject': f"Pedido {self.name}",
            'default_body': mail.html2plaintext(template.body_html),
            'default_whatsapp_number': self._format_waha_number(self.partner_id),
            'default_attachment_ids': [attachment.id],
        }

        return {
            'type': 'ir.actions.act_window',
            'name': 'Enviar por WhatsApp',
            'res_model': 'mail.compose.message',
            'views': [(self.env.ref('pedido_whatsapp.view_whatsapp_composer_wizard_form').id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_cancel(self):
        """
        Envia notificação de cancelamento automaticamente.
        """
        res = super().action_cancel()
        
        for order in self:
            try:
                template = self.env.ref('pedido_whatsapp.mail_template_sale_cancel')
                message_text = self.env['mail.template']._render_template(template.body_html, 'sale.order', order.ids)[order.id]
                clean_body = mail.html2plaintext(message_text)
                chat_id = order._format_waha_number(order.partner_id)
                order._send_whatsapp_message(chat_id, clean_body)
                order.message_post(body=_("Notificação de cancelamento enviada por WhatsApp."))
            except Exception as e:
                _logger.error("Falha ao enviar notificação de cancelamento para o pedido %s: %s", order.name, e)
        
        return res