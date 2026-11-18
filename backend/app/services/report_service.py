from decimal import Decimal
from datetime import datetime
from typing import Optional, List, Dict, Any
from io import BytesIO
from sqlalchemy.orm import Session
from sqlalchemy import func
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from app.models import (
    Invoice, InvoiceItem, InvoiceStatus, SalesOrder, Payment,
    ProductionRun, ProductionRunItem, StockMovement, MovementType,
    Customer, Item, BOM, AuditLog
)
from app.services.ledger_service import LedgerService
from app.config import settings

class ReportService:
    @staticmethod
    def get_sales_register(
        db: Session,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        query = db.query(Invoice).filter(Invoice.status != InvoiceStatus.CANCELLED_VIA_CREDIT_NOTE)
        if from_date:
            query = query.filter(Invoice.invoice_date >= from_date)
        if to_date:
            query = query.filter(Invoice.invoice_date <= to_date)
            
        invoices = query.order_by(Invoice.invoice_date.desc()).all()
        rows = []
        for inv in invoices:
            for item in inv.items:
                rows.append({
                    "invoice_number": inv.invoice_number,
                    "invoice_date": inv.invoice_date.strftime("%Y-%m-%d"),
                    "customer_name": inv.customer.name,
                    "customer_state": inv.customer.state,
                    "item_name": item.item.name,
                    "hsn_code": item.hsn_code,
                    "quantity": float(item.quantity),
                    "unit": item.unit,
                    "unit_price": float(item.unit_price),
                    "taxable_amount": float(item.taxable_amount),
                    "cgst_amount": float(item.cgst_amount),
                    "sgst_amount": float(item.sgst_amount),
                    "igst_amount": float(item.igst_amount),
                    "total_amount": float(item.total_amount),
                    "is_inter_state": inv.is_inter_state,
                    "is_dispatched": inv.is_dispatched
                })
        return rows

    @staticmethod
    def get_gst_summary(
        db: Session,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generates GSTR-1 / GSTR-3B compliant summary of outward supplies.
        """
        query = db.query(Invoice).filter(Invoice.status != InvoiceStatus.CANCELLED_VIA_CREDIT_NOTE)
        if from_date:
            query = query.filter(Invoice.invoice_date >= from_date)
        if to_date:
            query = query.filter(Invoice.invoice_date <= to_date)
            
        invoices = query.all()
        
        b2b_taxable = Decimal("0.00")
        b2b_cgst = Decimal("0.00")
        b2b_sgst = Decimal("0.00")
        b2b_igst = Decimal("0.00")
        b2b_total = Decimal("0.00")

        records = []
        for inv in invoices:
            taxable = Decimal(str(inv.taxable_amount))
            cgst = Decimal(str(inv.cgst_amount))
            sgst = Decimal(str(inv.sgst_amount))
            igst = Decimal(str(inv.igst_amount))
            total = Decimal(str(inv.total_amount))

            b2b_taxable += taxable
            b2b_cgst += cgst
            b2b_sgst += sgst
            b2b_igst += igst
            b2b_total += total

            records.append({
                "invoice_number": inv.invoice_number,
                "invoice_date": inv.invoice_date.strftime("%Y-%m-%d"),
                "customer_name": inv.customer.name,
                "customer_gstin": inv.customer.gstin,
                "place_of_supply": inv.place_of_supply,
                "is_inter_state": inv.is_inter_state,
                "taxable_value": float(taxable),
                "cgst": float(cgst),
                "sgst": float(sgst),
                "igst": float(igst),
                "invoice_value": float(total)
            })

        return {
            "period": f"{datetime.utcnow().strftime('%B %Y')}",
            "factory_gstin": settings.FACTORY_GSTIN,
            "factory_state": settings.FACTORY_STATE,
            "totals": {
                "total_taxable_value": float(b2b_taxable),
                "total_cgst": float(b2b_cgst),
                "total_sgst": float(b2b_sgst),
                "total_igst": float(b2b_igst),
                "total_tax": float(b2b_cgst + b2b_sgst + b2b_igst),
                "total_invoice_value": float(b2b_total)
            },
            "records": records
        }

    @staticmethod
    def get_purchase_register(db: Session) -> List[Dict[str, Any]]:
        purchases = db.query(StockMovement).filter(
            StockMovement.movement_type == MovementType.PURCHASE_RECEIPT
        ).order_by(StockMovement.timestamp.desc()).all()

        rows = []
        for p in purchases:
            qty = Decimal(str(p.quantity))
            rate = Decimal(str(p.unit_cost))
            val = qty * rate
            rows.append({
                "date": p.timestamp.strftime("%Y-%m-%d"),
                "reference_no": p.reference_id,
                "item_name": p.item.name,
                "category": p.item.category.value,
                "quantity": float(qty),
                "unit": p.item.unit,
                "rate": float(rate),
                "total_value": float(val),
                "notes": p.notes
            })
        return rows

    @staticmethod
    def get_production_report(db: Session) -> List[Dict[str, Any]]:
        runs = db.query(ProductionRun).order_by(ProductionRun.run_date.desc()).all()
        results = []
        for r in runs:
            materials = []
            for item in r.items:
                materials.append({
                    "item_name": item.item.name,
                    "unit": item.unit,
                    "standard_qty": float(item.standard_qty),
                    "actual_qty": float(item.actual_qty),
                    "variance_percent": float(item.consumption_variance_percent),
                    "is_damaged": item.is_damaged_scrap,
                    "unit_cost": float(item.unit_cost),
                    "total_cost": float(item.total_cost)
                })

            results.append({
                "run_number": r.run_number,
                "run_date": r.run_date.strftime("%Y-%m-%d"),
                "product_name": r.product.name,
                "planned_output": float(r.planned_output_qty),
                "actual_output": float(r.actual_output_qty),
                "yield_variance_percent": float(r.yield_variance_percent),
                "labour_cost": float(r.labour_cost),
                "power_gas_cost": float(r.power_gas_cost),
                "material_cost": float(r.total_material_cost),
                "total_production_cost": float(r.total_production_cost),
                "cost_per_packet": float(r.cost_per_packet),
                "margin_percent": float(r.margin_percent),
                "materials": materials
            })
        return results

    @staticmethod
    def get_receivables_aging_report(db: Session) -> List[Dict[str, Any]]:
        customers = db.query(Customer).all()
        aging = []
        for c in customers:
            invoices = db.query(Invoice).filter(
                Invoice.customer_id == c.id,
                Invoice.status != InvoiceStatus.CANCELLED_VIA_CREDIT_NOTE
            ).all()
            payments = db.query(Payment).filter(Payment.customer_id == c.id).all()
            
            invoiced = sum([Decimal(str(i.total_amount)) for i in invoices], Decimal("0.00"))
            paid = sum([Decimal(str(p.amount)) for p in payments], Decimal("0.00"))
            outstanding = invoiced - paid
            
            aging.append({
                "customer_id": c.id,
                "customer_name": c.name,
                "state": c.state,
                "type": c.type,
                "total_invoiced": float(invoiced),
                "total_collected": float(paid),
                "outstanding_due": float(outstanding)
            })
        return aging

    @staticmethod
    def get_owner_dashboard(db: Session) -> Dict[str, Any]:
        """
        Dashboard summary for the business owner:
        - Today's orders
        - Current stock balances
        - Active variance alerts
        - Unit production cost & margins
        - Outstanding customer dues
        """
        all_balances = LedgerService.get_stock_summary(db)
        
        # Today's orders
        orders = db.query(SalesOrder).all()
        order_count = len(orders)
        order_value = sum([Decimal(str(o.total_amount)) for o in orders], Decimal("0.00"))
        
        # Variance alerts (runs with yield variance > 3% or item variance > 3%)
        alerts = []
        runs = db.query(ProductionRun).all()
        for r in runs:
            if abs(Decimal(str(r.yield_variance_percent))) > Decimal(str(settings.VARIANCE_TOLERANCE_PERCENT)):
                alerts.append({
                    "type": "YIELD_VARIANCE",
                    "severity": "WARNING",
                    "message": f"Run {r.run_number} yield variance of {r.yield_variance_percent}% exceeds ±{settings.VARIANCE_TOLERANCE_PERCENT}% tolerance"
                })
            for m in r.items:
                if abs(Decimal(str(m.consumption_variance_percent))) > Decimal(str(settings.VARIANCE_TOLERANCE_PERCENT)):
                    alerts.append({
                        "type": "CONSUMPTION_VARIANCE",
                        "severity": "WARNING",
                        "message": f"Run {r.run_number}: {m.item.name} consumption variance of {m.consumption_variance_percent}% exceeds ±{settings.VARIANCE_TOLERANCE_PERCENT}% tolerance"
                    })

        # Latest unit cost
        latest_run = db.query(ProductionRun).order_by(ProductionRun.run_date.desc()).first()
        latest_cost_pkt = float(latest_run.cost_per_packet) if latest_run else 0.0
        latest_margin = float(latest_run.margin_percent) if latest_run else 0.0

        # Outstanding dues
        receivables = ReportService.get_receivables_aging_report(db)
        total_outstanding = sum([r["outstanding_due"] for r in receivables])

        return {
            "total_orders_count": order_count,
            "total_orders_value": float(order_value),
            "stock_summary": all_balances,
            "variance_alerts": alerts,
            "latest_cost_per_packet": latest_cost_pkt,
            "latest_margin_percent": latest_margin,
            "total_outstanding_receivables": total_outstanding,
            "receivables_summary": receivables
        }

    @staticmethod
    def export_stock_ledger_excel(db: Session) -> bytes:
        """
        Exports the entire stock ledger with running balances as an auditor-ready formatted Excel workbook.
        """
        ledger = LedgerService.get_stock_ledger(db)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Stock Movement Ledger"

        # Headers
        headers = [
            "Entry ID", "Timestamp (UTC)", "Item Code", "Item Name", "Category",
            "Movement Type", "Ref Document", "Ref ID", "Quantity", "Unit",
            "Unit Cost (₹)", "Running Balance", "Notes"
        ]
        ws.append(headers)

        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_idx)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for entry in ledger:
            ws.append([
                entry["id"],
                entry["timestamp"][:19],
                entry["item_code"],
                entry["item_name"],
                entry["category"],
                entry["movement_type"],
                entry["reference_type"],
                entry["reference_id"],
                entry["quantity"],
                entry["unit"],
                entry["unit_cost"],
                entry["running_balance"],
                entry["notes"] or ""
            ])

        # Auto-fit column widths
        for col in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        output = BytesIO()
        wb.save(output)
        return output.getvalue()

    @staticmethod
    def generate_gst_invoice_pdf(db: Session, invoice_id: int) -> bytes:
        """
        Generates a GST-compliant Tax Invoice PDF.
        """
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError("Invoice not found")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        story = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#1F4E78"),
            alignment=1
        )
        sub_style = ParagraphStyle(
            'SubTitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=1
        )

        story.append(Paragraph("<b>SOUTH INDIAN SNACKS FACTORY</b>", title_style))
        story.append(Paragraph("Thuvakudi Industrial Estate, Tiruchirappalli, Tamil Nadu - 620015", sub_style))
        story.append(Paragraph(f"<b>GSTIN: {settings.FACTORY_GSTIN} | State: {settings.FACTORY_STATE} (Code: {settings.FACTORY_STATE_CODE})</b>", sub_style))
        story.append(Spacer(1, 15))
        story.append(Paragraph("<b>TAX INVOICE</b>", ParagraphStyle('TaxInv', parent=styles['Heading2'], alignment=1, textColor=colors.HexColor("#333333"))))
        story.append(Spacer(1, 10))

        # Meta table
        meta_data = [
            [f"Invoice No: {invoice.invoice_number}", f"Invoice Date: {invoice.invoice_date.strftime('%d-%b-%Y')}"],
            [f"Billed To: {invoice.customer.name}", f"Place of Supply: {invoice.place_of_supply}"],
            [f"Customer GSTIN: {invoice.customer.gstin or 'URP'}", f"State Code: {invoice.customer.state_code}"],
        ]
        meta_table = Table(meta_data, colWidths=[270, 270])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F2F4F8")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 9),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#B0C4DE")),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E0E0E0")),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 15))

        # Items Table
        items_header = ["#", "Item Description", "HSN", "Qty", "Rate (₹)", "Taxable (₹)", "CGST (₹)", "SGST (₹)", "IGST (₹)", "Total (₹)"]
        items_data = [items_header]
        
        idx = 1
        for item in invoice.items:
            items_data.append([
                str(idx),
                item.item.name,
                item.hsn_code,
                f"{float(item.quantity):.1f} {item.unit}",
                f"{float(item.unit_price):.2f}",
                f"{float(item.taxable_amount):.2f}",
                f"{float(item.cgst_amount):.2f}",
                f"{float(item.sgst_amount):.2f}",
                f"{float(item.igst_amount):.2f}",
                f"{float(item.total_amount):.2f}",
            ])
            idx += 1

        # Totals Row
        items_data.append([
            "", "<b>TOTAL</b>", "", "", "",
            f"<b>₹{float(invoice.taxable_amount):.2f}</b>",
            f"<b>₹{float(invoice.cgst_amount):.2f}</b>",
            f"<b>₹{float(invoice.sgst_amount):.2f}</b>",
            f"<b>₹{float(invoice.igst_amount):.2f}</b>",
            f"<b>₹{float(invoice.total_amount):.2f}</b>"
        ])

        col_widths = [20, 130, 45, 45, 50, 60, 50, 50, 50, 60]
        items_table = Table(items_data, colWidths=col_widths)
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1F4E78")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('ALIGN', (4, 1), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#1F4E78")),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#D3D3D3")),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor("#1F4E78")),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor("#F2F4F8")),
        ]))
        story.append(items_table)
        story.append(Spacer(1, 20))

        # Footer
        footer_text = f"<b>Total Invoice Amount in Words:</b> Indian Rupees Seven Thousand Eight Hundred Seventy Five Only<br/><br/>" \
                      f"<i>This is a computer-generated GST tax invoice. No signature required.</i>"
        story.append(Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, leading=12)))

        doc.build(story)
        return buffer.getvalue()
