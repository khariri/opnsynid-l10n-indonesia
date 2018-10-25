# -*- coding: utf-8 -*-
# Copyright 2018 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, fields


class KBLapPosisiWipWizard(models.TransientModel):
    _name = "l10n_id.kb_lap_posisi_wip_wizard"
    _inherit = ["l10n_id.date_range_selector"]

    warehouse_ids = fields.Many2many(
        string="Warehouse",
        comodel_name="stock.warehouse",
        relation="rel_djbc_posisi_wip_2_warehouse",
        column1="wizard_id",
        column2="warehouse_id"
    )

    @api.multi
    def action_print_sreen(self):
        waction = self.env.ref(
            "laporan_posisi_wip.djbc_kb_lap_posisi_wip_action")
        criteria = [
            ("tgl_penerimaan", ">=", self.date_start),
            ("tgl_penerimaan", "<=", self.date_end),
            ("warehouse_id", "in", self.warehouse_ids.ids)
        ]
        waction.domain = criteria
        return waction.read()[0]