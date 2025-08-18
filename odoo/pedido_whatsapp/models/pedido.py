# odoo/pedido_whatsapp/models/pedido.py
import logging
from odoo import models, _, SUPERUSER_ID
from odoo.tools import mail
from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model, WhatsappApiMixin):
    _inherit = 'sale.order'
    _description = 'Pedido de Venda com Integração WhatsApp'

    def action_open_send_pdf_wizard(self):
        """
        Esta função abre a janela (wizard) para o usuário anexar e enviar o PDF.
        """
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Enviar PDF Anexado para API',
            'res_model': 'sale.order.send_pdf.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_order_name': self.name,
            },
        }

    # --- FUNÇÕES ANTIGAS QUE JÁ FUNCIONAVAM ---

    def action_enviar_whatsapp_cotacao(self):
        """
        Envia a cotação como mensagem de TEXTO.
        """
        self.ensure_one()
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_quotation')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Cotação (texto) enviada por WhatsApp."))
        return {'effect': {'fadeout': 'slow', 'message': 'Cotação enviada com sucesso!', 'type': 'rainbow_man'}}

    def action_enviar_whatsapp_confirmacao(self):
        """
        Envia a confirmação de venda como mensagem de TEXTO.
        """
        self.ensure_one()
        # Usa o template de confirmação
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_confirmation')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Confirmação de Venda enviada por WhatsApp."))
        return {'effect': {'fadeout': 'slow', 'message': 'Confirmação enviada com sucesso!', 'type': 'rainbow_man'}}
    
    def _get_whatsapp_message(self, template_xml_id):
        """
        Função auxiliar para renderizar o template de mensagem.
        """
        self.ensure_one()
        template = self.env.ref(template_xml_id)
        message_html = template._render_template(template.body_html, 'sale.order', self.ids)[self.id]
        return mail.html2plaintext(message_html)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        return res

    def action_cancel(self):
        res = super().action_cancel()
        return res