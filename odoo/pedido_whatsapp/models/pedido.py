# odoo/pedido_whatsapp/models/pedido.py
import logging
import base64
from odoo import models, _, SUPERUSER_ID
from odoo.tools import mail
from odoo.exceptions import UserError

from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

# Usamos a herança mista que NÃO QUEBRA o servidor
class SaleOrder(models.Model, WhatsappApiMixin):
    _description = 'Pedido de Venda com Integração WhatsApp'
    # Usamos o _inherit como string simples
    _inherit = 'sale.order'

    def _get_whatsapp_message(self, template_xml_id):
        self.ensure_one()
        template = self.env.ref(template_xml_id)
        message_html = template._render_template(template.body_html, 'sale.order', self.ids)[self.id]
        return mail.html2plaintext(message_html)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        try:
            message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_confirmation')
            chat_id = self._format_waha_number(self.partner_id)
            self._send_whatsapp_message(chat_id, message_text)
            self.message_post(body=_("Notificação de confirmação enviada por WhatsApp."))
        except Exception as e:
            _logger.error("Falha ao enviar notificação de confirmação por WhatsApp: %s", e)
        return res

    def action_enviar_whatsapp_cotacao(self):
        self.ensure_one()
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_quotation')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Cotação enviada por WhatsApp."))
        return {'effect': {'fadeout': 'slow', 'message': 'Cotação enviada com sucesso!', 'type': 'rainbow_man'}}

    def action_enviar_whatsapp_pdf(self):
        self.ensure_one()
        composer = self.env['mail.compose.message'].with_context({
            'default_model': 'sale.order',
            'default_res_ids': [self.id], # Sintaxe correta para Odoo 17
            'default_use_template': False,
            'default_template_id': False,
            'default_composition_mode': 'comment',
        }).create({})
        composer.action_send_mail()
        attachment = self.env['ir.attachment'].search([
            ('res_model', '=', 'sale.order'),
            ('res_id', '=', self.id)
        ], order='create_date desc', limit=1)
        if not attachment:
            raise UserError(_("Não foi possível gerar ou encontrar o anexo do PDF."))
        pdf_base64 = attachment.datas.decode('utf-8')
        file_name = attachment.name
        mimetype = attachment.mimetype
        caption = f"Olá, {self.partner_id.name}! Segue em anexo o seu orçamento."
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_document(chat_id, file_name, pdf_base64, mimetype, caption)
        self.message_post(body=_("Orçamento em PDF enviado por WhatsApp."))
        return {'effect': {'fadeout': 'slow', 'message': 'PDF do orçamento enviado com sucesso!', 'type': 'rainbow_man'}}

    def action_enviar_whatsapp_cancelado(self):
        self.ensure_one()
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_cancel')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Notificação de cancelamento enviada por WhatsApp."))
        return True

    def action_cancel(self):
        res = super().action_cancel()
        try:
            self.action_enviar_whatsapp_cancelado()
        except Exception as e:
            _logger.error("Falha ao enviar notificação de cancelamento por WhatsApp: %s", e)
        return res