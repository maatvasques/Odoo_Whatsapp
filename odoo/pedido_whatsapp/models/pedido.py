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
        self.ensure_one()
        
        # 1. Gera o PDF
        report = self.env.ref('sale.action_report_saleorder').with_user(SUPERUSER_ID)
        pdf_bytes, content_type = report._render_qweb_pdf([self.id])
        
        # 2. Cria um anexo temporário com o PDF para o pop-up
        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}.pdf",
            'type': 'binary',
            'datas': base64.b64encode(pdf_bytes),
            'res_model': 'mail.compose.message',
            'res_id': 0,
            'mimetype': 'application/pdf',
        })

        # 3. Escolhe o template de mensagem (Cotação ou Confirmação)
        template_xml_id = 'pedido_whatsapp.mail_template_sale_quotation'
        if self.state in ['sale', 'done']:
            template_xml_id = 'pedido_whatsapp.mail_template_sale_confirmation'
        
        template = self.env.ref(template_xml_id)
        
        # 4. Prepara os dados para pré-preencher o pop-up
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_composition_mode': 'comment',
            'default_body': mail.html2plaintext(template.body_html),
            'default_whatsapp_number': self._format_waha_number(self.partner_id),
            'default_attachment_ids': [attachment.id],
        }

        # 5. Abre o pop-up
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enviar por WhatsApp',
            'res_model': 'mail.compose.message',
            'views': [(self.env.ref('pedido_whatsapp.view_whatsapp_composer_form').id, 'form')],
            'target': 'new',
            'context': ctx,
        }

    def action_cancel(self):
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