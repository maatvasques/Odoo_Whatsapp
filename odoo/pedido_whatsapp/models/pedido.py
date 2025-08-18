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
        Esta função é o coração da nova funcionalidade.
        Ela prepara e abre o wizard com o contexto correto (cotação ou confirmação).
        """
        self.ensure_one()
        
        # 1. Gerar o PDF da cotação/pedido
        report = self.env.ref('sale.action_report_saleorder').with_user(SUPERUSER_ID)
        pdf_bytes, content_type = report._render_qweb_pdf([self.id])
        pdf_base64 = base64.b64encode(pdf_bytes)

        # 2. Criar um anexo temporário com o PDF gerado
        attachment = self.env['ir.attachment'].create({
            'name': f"{self.name}.pdf",
            'type': 'binary',
            'datas': pdf_base64,
            'res_model': 'mail.compose.message',
            'res_id': 0,
            'mimetype': 'application/pdf',
        })

        # 3. LÓGICA INTELIGENTE: Escolhe o template de mensagem baseado no status do pedido
        if self.state in ['draft', 'sent']:
            # Se for um orçamento, usa o template de cotação
            template_xml_id = 'pedido_whatsapp.mail_template_sale_quotation'
        else: # Se já for um pedido de venda ('sale' ou 'done'), usa o de confirmação
            template_xml_id = 'pedido_whatsapp.mail_template_sale_confirmation'
        
        template = self.env.ref(template_xml_id)
        
        # 4. Preparar o "contexto" para pré-preencher a janela do wizard
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.id,
            'default_use_template': False,
            'default_template_id': None,
            'default_composition_mode': 'comment',
            'default_subject': f"Pedido {self.name}", # Assunto pré-preenchido
            'default_body': mail.html2plaintext(template.body_html), # Corpo da mensagem
            'default_whatsapp_number': self._format_waha_number(self.partner_id), # Número do cliente
            'default_attachment_ids': [attachment.id], # PDF pré-anexado
        }

        # 5. Retorna a ação que abre a janela do wizard
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
        Sobrescreve a ação de cancelar para enviar uma notificação de WhatsApp automaticamente.
        """
        res = super().action_cancel()
        
        for order in self:
            try:
                message_text = order.env.ref('pedido_whatsapp.mail_template_sale_cancel').body_html
                rendered_body = self.env['mail.template']._render_template(message_text, 'sale.order', order.ids, post_process=True)[order.id]
                clean_body = mail.html2plaintext(rendered_body)

                chat_id = order._format_waha_number(order.partner_id)
                order._send_whatsapp_message(chat_id, clean_body)
                
                order.message_post(body=_("Notificação de cancelamento enviada por WhatsApp."))
            except Exception as e:
                _logger.error("Falha ao enviar notificação de cancelamento para o pedido %s: %s", order.name, e)
                order.message_post(body=_("Falha ao enviar notificação de cancelamento por WhatsApp: %s", e))
        
        return res

    # As funções abaixo são herdadas do mixin e não precisam estar aqui,
    # mas as mantemos caso queira customizar algo no futuro.
    # Se quiser um código mais limpo, elas podem ser removidas deste arquivo.
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        return res