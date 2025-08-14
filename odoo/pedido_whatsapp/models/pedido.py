# odoo/pedido_whatsapp/models/pedido.py
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

        # --- CORREÇÃO FINAL E DEFINITIVA AQUI ---
        # 1. Criamos um novo ambiente de execução com o usuário SUPERUSER.
        #    Isso garante que todas as operações seguintes ignorem as regras de acesso.
        sudo_env = self.env(user=SUPERUSER_ID)
        
        # 2. Usamos este ambiente para buscar o relatório de forma segura.
        report_template = sudo_env['ir.actions.report'].search([
            ('model', '=', 'sale.order'),
            ('report_type', '=', 'qweb-pdf')
        ], limit=1)

        if not report_template:
            raise UserError(_("Nenhum relatório PDF para Pedidos de Venda foi encontrado no sistema."))

        # 3. Renderizamos o PDF passando o ID como um NÚMERO ÚNICO (self.id)
        #    para evitar o erro de 'lista'.
        pdf_content, content_type = report_template._render_qweb_pdf(self.id)
        # --- FIM DA CORREÇÃO ---

        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        file_name = f"{self.name}.pdf"
        caption = f"Olá, {self.partner_id.name}! Segue em anexo o seu orçamento."

        # Retornamos à função de envio para a API externa (WorkWise)
        self._send_document_to_workwise(file_name, base64.b64decode(pdf_base64), self.name)
        
        self.message_post(body=_("Orçamento em PDF enviado para a API Externa."))
        
        return {
            'effect': { 'fadeout': 'slow', 'message': 'PDF do orçamento enviado com sucesso!', 'type': 'rainbow_man' }
        }

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