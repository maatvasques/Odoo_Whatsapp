# -*- coding: utf-8 -*-
import logging
import re
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

class WhatsappWebhook(http.Controller):

    # O @http.route define nossa URL pública (o "endereço" para a WAHA)
    @http.route('/whatsapp/webhook', type='json', auth='public', csrf=False)
    def webhook(self, **kwargs):
        # O Odoo converte o JSON recebido em um dicionário Python
        data = request.jsonrequest
        _logger.info(">>> Webhook recebido da WAHA: %s", data)

        # Estrutura de um evento de nova mensagem da WAHA
        if data.get('event') == 'message' and data.get('payload'):
            payload = data['payload']
            message_body = payload.get('body')
            chat_id = payload.get('from') # O número de quem enviou

            if not message_body or not chat_id:
                _logger.warning("Webhook de mensagem sem corpo ou remetente.")
                return {'status': 'ignored'}

            # 1. Limpar o número de telefone para procurar no banco
            # Remove o "@c.us" e qualquer outro caractere não numérico
            clean_number = re.sub(r'\D', '', chat_id)
            # Remove o DDI '55' do Brasil, se presente no início, para bater com formatos
            # de cadastro mais comuns (ex: (11) 99999-8888)
            if clean_number.startswith('55'):
                search_number = clean_number[2:]
            else:
                search_number = clean_number

            _logger.info("Procurando parceiro com o número: %s", search_number)

            # 2. Procurar o parceiro (cliente) no banco de dados
            # Usamos sudo() porque o usuário 'public' não tem permissão para ler contatos
            Partner = request.env['res.partner'].sudo()
            # Procura por um número que TERMINE com o número limpo, para cobrir
            # formatos com ou sem DDD, etc. Ex: busca por "11999998888"
            partner = Partner.search([
                '|',
                ('phone', 'like', search_number),
                ('mobile', 'like', search_number)
            ], limit=1)

            # 3. Se o parceiro for encontrado, registrar a mensagem no Chatter
            if partner:
                _logger.info("Parceiro encontrado: %s (ID: %s)", partner.name, partner.id)
                # message_post é a função mágica que adiciona ao histórico
                partner.message_post(
                    body=f"Mensagem recebida via WhatsApp: {message_body}",
                    message_type='comment',
                    subtype_xmlid='mail.mt_comment',
                )
                return {'status': 'ok'}
            else:
                _logger.warning("Nenhum parceiro encontrado para o número: %s", search_number)
                return {'status': 'partner not found'}

        return {'status': 'event ignored'}