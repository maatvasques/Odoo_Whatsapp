# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    order_date_related = fields.Datetime(
        related='order_id.date_order',
        string='Data do Pedido',
        store=True
    )