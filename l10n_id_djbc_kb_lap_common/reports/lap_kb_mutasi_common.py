# -*- coding: utf-8 -*-
# Copyright 2018 OpenSynergy Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from openerp import models, fields, api
from openerp import tools


class LapKbMutasiCommon(models.AbstractModel):
    _name = "l10n_id.djbc_kb_lap_mutasi_common"
    _description = "Common Model for Laporan Mutasi Kawasan Berikat"
    _auto = False

    @api.multi
    def _qty_from(self):
        self.ensure_one()
        str_select = """
        FROM stock_move AS a
        JOIN stock_picking_type AS b ON a.picking_type_id = b.id
        JOIN stock_location AS c ON a.location_id = c.id
        JOIN stock_location AS d ON a.location_dest_id =d.id
        """
        return str_select

    @api.multi
    def _qty_where(
        self, date_start, date_end, movement_type="in",
        scrap=False, adjustment=False
    ):
        self.ensure_one()
        str_where = """
        WHERE
            a.product_id = %s AND
            b.warehouse_id = %s AND
            b.djbc_kb_movement_type = '%s' AND
            b.djbc_kb_scrap %s AND
            a.state = 'done' 
        """ % (
            self.product_id.id,
            self.warehouse_id.id,
            movement_type,
            scrap and 'IS TRUE' or 'IS FALSE',
        )
        tgl_now = datetime.datetime.now();
        if date_start:
            str_where += """
            AND a.date >= '%s' AND
            a.date <= '%s'
            """ % (date_start, date_end)
        else:
            str_where += """
            AND a.date < '%s'
            """ % (date_end)
        # str_where = """
        # WHERE
        #     a.product_id = %s AND
        #     b.warehouse_id = %s AND
        #     b.djbc_kb_movement_type = '%s' AND
        #     b.djbc_kb_scrap %s AND
        #     a.state = 'done' AND
        # """ % (
        #     self.product_id.id,
        #     self.warehouse_id.id,
        #     movement_type,
        #     scrap and 'IS TRUE' or 'IS FALSE',
        # )
        # if date_start:
        #     str_where += """
        #     a.date >= '%s' AND
        #     a.date <= '%s'
        #     """ % (date_start, date_end)
        # else:
        #     str_where += """
        #     a.date < '%s'
        #     """ % (date_end)
        if adjustment:
            str_where += """
             AND (a.inventory_id != %s OR 
             a.inventory_id IS NULL)
            """ % (adjustment)

        return str_where

    @api.multi
    def _qty_join(self):
        self.ensure_one()
        pass

    @api.multi
    def _qty_select(self):
        self.ensure_one()
        str_select = """
        SELECT
            a.product_qty AS qty
        """
        return str_select

    @api.multi
    def _compute_qty(self):
        date_start = self._context.get("date_start", False)
        date_end = self._context.get("date_end", False)
        obj_inv_line = self.env["stock.inventory.line"]
        obj_inv = self.env["stock.inventory"]

        for lap in self:
            saldo_awal = pemasukan = pengeluaran = \
                penyesuaian = saldo_akhir = stock_opname = \
                selisih = 0.0

            # Adjustment
            inv = False
            view_root_id = lap.warehouse_id.view_location_id.id
            criteria1 = [
                ("date", ">=", date_start),
                ("date", "<=", date_end),
                ("state", "=", "done"),
                ("djbc", "=", True),
                ("location_id.id", "child_of", view_root_id),
            ]
            invs = obj_inv.search(criteria1, order="date desc", limit=1)
            if invs:
                inv = invs[0]

            saldo_awal_pemasukan = lap._get_qty(
                False, date_start, "in", False, False)
            saldo_awal_pengeluaran = lap._get_qty(
                False, date_start, "out", False, False)
            saldo_awal = saldo_awal_pemasukan - saldo_awal_pengeluaran
            pemasukan = lap._get_qty(
                date_start, date_end, "in", False, inv and inv.id or False)
            pengeluaran = lap._get_qty(
                date_start, date_end, "out", False, inv and inv.id or False)

            if inv:
                criteria = [
                    ("inventory_id", "=", inv.id),
                    ("product_id", "=", lap.product_id.id),
                ]
                for inv_line in obj_inv_line.search(criteria):
                    stock_opname += inv_line.product_qty
                    penyesuaian += (inv_line.product_qty -
                                    inv_line.theoretical_qty)

            saldo_akhir = saldo_awal + pemasukan - pengeluaran + penyesuaian
            selisih = saldo_akhir - stock_opname

            if stock_opname == saldo_akhir:
                keterangan = "sesuai"
            elif saldo_akhir > stock_opname:
                keterangan = "lebih"
            else:
                keterangan = "kurang"

            lap.saldo_awal = saldo_awal
            lap.stock_opname = stock_opname
            lap.pemasukan = pemasukan
            lap.pengeluaran = pengeluaran
            lap.saldo_akhir = saldo_akhir
            lap.penyesuaian = penyesuaian
            lap.selisih = selisih
            lap.keterangan = keterangan

    @api.multi
    def _get_qty(self, date_start, date_end, movement_type, scrap, adjustment):
        self.ensure_one()
        result = 0.0
        # pylint: disable=locally-disabled, sql-injection
        str_sql = """
        %s
        %s
        %s
        """ % (
            self._qty_select(),
            self._qty_from(),
            self._qty_where(
                date_start,
                date_end,
                movement_type,
                scrap,
                adjustment
            )
        )
        self.env.cr.execute(str_sql)
        a = self.env.cr.dictfetchall()
        for row in a:
            result += row["qty"]
        return result

    kode_barang = fields.Char(
        string="Kode Barang",
        readonly=True,
    )
    product_id = fields.Many2one(
        string="Nama Barang",
        comodel_name="product.product",
        readonly=True,
    )
    uom_id = fields.Many2one(
        string="Satuan",
        comodel_name="product.uom",
        readonly=True,
    )
    #tambhaan hr
    # tgl_stock_move = fields.Char(
    #     string="Tanggal Penerimaan",
    #     readonly=True,
    # )
    #end
    saldo_awal = fields.Float(
        string="Saldo Awal",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    pemasukan = fields.Float(
        string="Pemasukan",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    pengeluaran = fields.Float(
        string="Pengeluaran",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    penyesuaian = fields.Float(
        string="Penyesuaian",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    stock_opname = fields.Float(
        string="Stock Opname",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    saldo_akhir = fields.Float(
        string="Saldo Buku",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    selisih = fields.Float(
        string="Selisih",
        readonly=True,
        compute="_compute_qty",
        store=False,
    )
    keterangan = fields.Selection(
        string="Ket",
        compute="_compute_qty",
        store=False,
        selection=[
            ("sesuai", "Sesuai"),
            ("kurang", "Selisih Kurang"),
            ("lebih", "Selisih Lebih"),
        ],
    )
    warehouse_id = fields.Many2one(
        string="Warehouse",
        comodel_name="stock.warehouse",
    )

    def _select(self):
        select_str = """
             SELECT row_number() OVER() as id,
                    a.default_code AS kode_barang,
                    a.id AS product_id,
                    b.uom_id AS uom_id,
                    stock_warehouse.id AS warehouse_id
        """
        return select_str

    def _from(self):
        from_str = """
                product_product AS a
        """
        return from_str

    def _where(self):
        where_str = """
        """
        return where_str
    # asli mas andit
    def _join(self):
        join_str = """
        CROSS JOIN stock_warehouse
        JOIN product_template AS b
            ON a.product_tmpl_id = b.id
        """
        return join_str

    #improv hariri
    # def _join(self):
    #     join_str = """
    #     CROSS JOIN stock_warehouse
    #     JOIN product_template AS b
    #         ON a.product_tmpl_id = b.id
    #     LEFT JOIN stock_move AS x
    #         ON a.id = x.product_id        
    #     """
    #     return join_str

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        # pylint: disable=locally-disabled, sql-injection
        cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM %s
            %s
            %s
        )""" % (
            self._table,
            self._select(),
            self._from(),
            self._join(),
            self._where()
        ))
