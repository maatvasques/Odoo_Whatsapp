# -*- coding: utf-8 -*-
import logging
from odoo import models, _
# --- ADIÇÃO IMPORTANTE AQUI ---
# Importamos a biblioteca de ferramentas de email do Odoo
from odoo.tools import mail

# Importamos o Mixin diretamente
from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

# Usamos a herança mista (Python + Odoo)
class SaleOrder(models.Model, WhatsappApiMixin):
    _description = 'Pedido de Venda com Integração WhatsApp'
    # Usamos o _inherit como string para estender o modelo
    _inherit = 'sale.order'

    def _get_whatsapp_message(self, template_xml_id):
        """
        Função auxiliar para renderizar o template e remover tags HTML.
        """
        self.ensure_one()
        template = self.env.ref(template_xml_id)
        
        # Renderiza o template para substituir as variáveis {{ ... }}
        message_html = template._render_template(
            template.body_html, 'sale.order', self.ids
        )[self.id]
        
        # --- CORREÇÃO FINAL E VERIFICADA AQUI ---
        # Usa a função correta 'html2plaintext' para converter HTML em texto puro
        return mail.html2plaintext(message_html)

    def action_enviar_whatsapp_cotacao(self):
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