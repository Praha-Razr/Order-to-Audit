from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from typing import Dict, Any

from app.database import get_db
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports & Auditor Exports"])

@router.get("/dashboard")
def get_owner_dashboard(db: Session = Depends(get_db)):
    """
    Returns owner dashboard KPIs: Today's orders, Stock levels, Variance alerts, Cost/packet, Outstanding dues.
    """
    return ReportService.get_owner_dashboard(db)

@router.get("/sales-register")
def get_sales_register(db: Session = Depends(get_db)):
    return ReportService.get_sales_register(db)

@router.get("/gst-summary")
def get_gst_summary(db: Session = Depends(get_db)):
    """
    GSTR-1 / GSTR-3B compliant summary with Place of Supply and split taxes.
    """
    return ReportService.get_gst_summary(db)

@router.get("/purchase-register")
def get_purchase_register(db: Session = Depends(get_db)):
    return ReportService.get_purchase_register(db)

@router.get("/production-report")
def get_production_report(db: Session = Depends(get_db)):
    return ReportService.get_production_report(db)

@router.get("/receivables-aging")
def get_receivables_aging(db: Session = Depends(get_db)):
    return ReportService.get_receivables_aging_report(db)

@router.get("/export/ledger/excel")
def export_ledger_excel(db: Session = Depends(get_db)):
    """
    Downloads full stock ledger as an Excel spreadsheet for the auditor.
    """
    excel_bytes = ReportService.export_stock_ledger_excel(db)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=stock_ledger.xlsx"}
    )

@router.get("/export/tally/xml")
def export_tally_xml(db: Session = Depends(get_db)):
    """
    Exports all vouchers in Tally XML import format.
    """
    xml_str = ReportService.export_tally_xml(db)
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=tally_import.xml"}
    )

@router.get("/invoices/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: int, db: Session = Depends(get_db)):
    """
    Downloads GST tax invoice as a PDF.
    """
    try:
        pdf_bytes = ReportService.generate_gst_invoice_pdf(db, invoice_id)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=invoice_{invoice_id}.pdf"}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
