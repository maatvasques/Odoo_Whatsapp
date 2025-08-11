# -*- coding: utf-8 -*-
{
    'name': "Integração de Pedidos com WhatsApp",
    'summary': """Envia notificações de pedidos de venda via WhatsApp.""",
    'description': """
        Adiciona botões e lógica ao Pedido de Venda para enviar notificações
        de cotação, confirmação e cancelamento usando o whatsapp_core.
    """,
    'author': "Seu Nome",
    'website': "https://www.seusite.com",
    'category': 'Sales',
    'version': '17.0.1.0.0',

    # A parte mais importante!
    # Garante que o Odoo carregue o App de Vendas e o nosso motor ANTES deste módulo.
    'depends': [
        'sale_management', # App de Vendas e suas dependências
        'whatsapp_core',   # Nosso motor!
    ],

    # Diz ao Odoo para carregar nossos arquivos de dados e views
    'data': [
        'data/mail_template_data.xml',
        'views/sale_order_views_inherited.xml',
    ],
    'installable': True,
    'application': True, # Marcamos como aplicação para aparecer em destaque
    'auto_install': False,
}