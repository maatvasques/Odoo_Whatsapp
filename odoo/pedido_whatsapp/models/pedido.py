# odoo/pedido_whatsapp/models/pedido.py
import logging
import requests
from odoo import models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools import mail
from odoo.addons.whatsapp_core.models.whatsapp_mixin import WhatsappApiMixin

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model, WhatsappApiMixin):
    _inherit = 'sale.order'
    _description = 'Pedido de Venda com Integração WhatsApp'

    def _send_document_to_workwise(self, file_name, pdf_bytes):
        """
        Envia o PDF para a API da WorkWise com dados hardcoded para teste.
        """
        workwise_url = "https://hmlapi.workwise.com.br/upload"
        # ATENÇÃO: Lembre-se de usar o seu token real aqui.
        workwise_token = "MEU_TOKEN_SUPER_SEGURO" 
        order_name = self.name

        headers = {'Authorization': f'Bearer {workwise_token}'}
        files = {'file': (file_name, pdf_bytes, 'application/pdf')}
        data = {'order_name': order_name}

        _logger.info("Enviando para a API WorkWise. URL: %s, Order: %s", workwise_url, order_name)
        try:
            response = requests.post(workwise_url, headers=headers, files=files, data=data, timeout=30)
            _logger.info("Resposta da API: %s - %s", response.status_code, response.text)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            error_message = _("Falha ao enviar o documento para a API Externa.\n\nDetalhe: %s")
            raise UserError(error_message % str(e))

    def action_enviar_whatsapp_pdf(self):
        self.ensure_one()

        # Voltamos a usar self.id (um número) em vez de [self.id] (uma lista)
        # para corrigir o erro "'list' object has no attribute 'split'"
        report = self.env.ref('sale.action_report_saleorder').with_user(SUPERUSER_ID)
        
        try:
            pdf_bytes, content_type = report._render_qweb_pdf(self.id)
        except Exception as e:
            _logger.error("Falha ao renderizar o PDF: %s", e, exc_info=True)
            error_message = _("Ocorreu um erro inesperado ao gerar o PDF. Verifique os logs. Detalhe: %s")
            raise UserError(error_message % e)
        
        # Chama a função de envio com o PDF gerado
        self._send_document_to_workwise(f"{self.name}.pdf", pdf_bytes)

        self.message_post(body=_("Orçamento em PDF enviado para a API Externa."))
        
        return {
            'effect': {'fadeout': 'slow', 'message': 'PDF do orçamento enviado com sucesso!', 'type': 'rainbow_man'}
        }


    # --- Funções restantes sem alteração ---
    def action_enviar_whatsapp_cotacao(self):
        self.ensure_one()
        message_text = self._get_whatsapp_message('pedido_whatsapp.mail_template_sale_quotation')
        chat_id = self._format_waha_number(self.partner_id)
        self._send_whatsapp_message(chat_id, message_text)
        self.message_post(body=_("Cotação enviada por WhatsApp."))
        return {'effect': {'fadeout': 'slow', 'message': 'Cotação enviada com sucesso!', 'type': 'rainbow_man'}}

    def _get_whatsapp_message(self, template_xml_id):
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