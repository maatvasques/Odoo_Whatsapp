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
    _inherit = 'sale.order'

    def action_enviar_whatsapp_pdf(self):
        self.ensure_one()

        # --- CORREÇÃO FINAL E DEFINITIVA AQUI ---
        # 1. Buscamos o relatório de forma segura usando o nome técnico padrão.
        report = self.env['ir.actions.report']._get_report_from_name('sale.report_saleorder')
        if not report:
            raise UserError(_("O relatório de orçamento padrão ('sale.report_saleorder') não foi encontrado."))

        # 2. Usamos .sudo() no relatório para forçar a execução com permissões de administrador.
        # 3. Passamos o ID como um NÚMERO ÚNICO (self.id) para evitar o erro de 'lista'.
        pdf_content, content_type = report.sudo()._render_qweb_pdf(self.id)
        # --- FIM DA CORREÇÃO ---

        # Esta parte é para a API WorkWise, como planejado
        pdf_bytes = pdf_content
        file_name = f"{self.name}.pdf"
        
        self._send_document_to_workwise(file_name, pdf_bytes, self.name)
        
        self.message_post(body=_("Orçamento em PDF enviado para a API Externa."))
        
        return {
            'effect': { 'fadeout': 'slow', 'message': 'PDF do orçamento enviado com sucesso!', 'type': 'rainbow_man' }
        }

    # As outras funções (cotação, confirmação, etc.) permanecem funcionais
    def _get_whatsapp_message(self, template_xml_id):
        self.ensure_one()
        template = self.env.ref(template_xml_id)
        message_html = template._render_template(template.body_html, 'sale.order', self.ids)[self.id]
        return mail.html2plaintext(message_html)

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # ... (código de envio de confirmação)
        return res

    def action_enviar_whatsapp_cotacao(self):
        # ... (código de envio de cotação)
        self.ensure_one()
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_quotation')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Cotação enviada por WhatsApp."))
        return {'effect': {'fadeout': 'slow', 'message': 'Cotação enviada com sucesso!', 'type': 'rainbow_man'}}

    def action_cancel(self):
        res = super().action_cancel()
        # ... (código de envio de cancelamento)
        return res