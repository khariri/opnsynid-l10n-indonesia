# -*- coding: utf-8 -*-
# Copyright 2017 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields
from openerp import tools


class LapKbPosisiWip(models.Model):
    _name = "l10n_id.djbc_kb_lap_posisi_wip"
    _description = "Laporan Posisi WIP Untuk Kawasan Berikat"
    _auto = False

    tgl_penerimaan = fields.Char(
        string="Tanggal Penerimaan"
    )

    kode_barang = fields.Char(
        string="Kode Barang"
    )

    nama_barang = fields.Many2one(
        string="Nama Barang",
        comodel_name="product.product"
    )

    jumlah = fields.Float(
        string="Jumlah"
    )

    satuan = fields.Many2one(
        string="Satuan",
        comodel_name="product.uom"
    )

    warehouse_id = fields.Many2one(
        string="Warehouse",
        comodel_name="stock.warehouse"
    )

    def _select(self):
        select_str = """
            SELECT  a.id as id,
                C.id as id_mo,
                A.date as tgl_penerimaan,
                D.default_code as kode_barang,
                A.product_id as nama_barang,
                A.product_qty as jumlah,
                A.product_uom as satuan,
                A.warehouse_id AS warehouse_id
        """
        return select_str

    def _from(self):
        from_str = """
            FROM stock_move AS A
        """
        return from_str

    def _where(self):
        where_str = """
            WHERE A.state='done' AND
                  C.state='in_production'
        """
        return where_str

    def _join(self):
        join_str = """
            LEFT JOIN mrp_production AS C ON A.name=C.name
            JOIN product_product AS D ON A.product_id=D.id          
        """
        return join_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        # pylint: disable=locally-disabled, sql-injection
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            %s
            %s
            %s
        )""" % (
            self._table,
            self._select(),
            self._from(),
            self._join(),
            self._where()
        ))
