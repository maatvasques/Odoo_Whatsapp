# odoo/pedido_whatsapp/models/account_move.py
# -*- coding: utf-8 -*-
import logging
import base64
from odoo import models, _, SUPERUSER_ID
from odoo.exceptions import UserError

# Importamos o nosso Mixin diretamente
from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

# Usamos a herança mista (Python + Odoo) que é estável no seu ambiente
class AccountMove(models.Model, WhatsappApiMixin):
    _description = 'Fatura com Integração WhatsApp'
    # Usamos o _inherit como uma string simples
    _inherit = 'account.move'

    def action_enviar_whatsapp_fatura_pdf(self):
        self.ensure_one()

        if self.state != 'posted':
            raise UserError(_("A fatura precisa estar no estado 'Lançado' para ser enviada."))

        # Usamos o método seguro para buscar o relatório pelo nome técnico
        report = self.env['ir.actions.report']._get_report_from_name('account.report_invoice_with_payments')
        if not report:
            raise UserError(_("O relatório de fatura padrão ('account.report_invoice_with_payments') não foi encontrado."))

        # Geramos o PDF usando o método seguro com .sudo()
        pdf_content, content_type = report.sudo()._render_qweb_pdf(self.id)

        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        file_name = f"Fatura-{self.name}.pdf".replace('/', '_')
        caption = f"Olá, {self.partner_id.name}! Segue em anexo a sua fatura."

        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_document(chat_id, file_name, pdf_base64, caption)
        
        self.message_post(body=_("Fatura em PDF enviada por WhatsApp."))
        
        return {
            'effect': { 'fadeout': 'slow', 'message': 'PDF da Fatura enviado com sucesso!', 'type': 'rainbow_man' }
        }