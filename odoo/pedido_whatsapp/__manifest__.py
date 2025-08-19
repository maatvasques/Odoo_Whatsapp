# -*- coding: utf-8 -*-
{
    'name': "Integração de Pedidos com WhatsApp",
    'summary': """Envia notificações de pedidos de venda via WhatsApp.""",
    'description': """...""",
    'author': "Seu Nome",
    'website': "https://www.seusite.com",
    'category': 'Sales',
    'version': '17.0.1.0.0',
    'depends': [
        'sale_management',
        'whatsapp_core',
        'mail',  # A dependência CRÍTICA
    ],
    'data': [
        'views/sale_order_views_inherited.xml',
        'wizard/whatsapp_composer_wizard_views.xml',
        'data/mail_template_data.xml',
        'views/sale_order_views_inherited.xml',
        'views/sale_order_graph_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}