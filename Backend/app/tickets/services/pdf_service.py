import io
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from app.utils import BASE_PATH, LOGO_PATH

class PDFService:
    @staticmethod
    def generate_ticket_pdf(event_data: dict, user_data: dict, booking_id: str) -> io.BytesIO:
        """
        Generates a PDF ticket for an event.
        """
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        # Draw Border
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(1)
        c.rect(15 * mm, height - 140 * mm, width - 30 * mm, 125 * mm)

        # Logo and Branding
        try:
            # Load logo (adjust path as needed depending on where you store it in backend container)
            # If running in Docker, keep in mind relative paths. 
            # We will use a try-except to safely skip if missing.
            if LOGO_PATH.exists():
                logo = ImageReader(str(LOGO_PATH))
                c.drawImage(logo, 20 * mm, height - 35 * mm, width=40 * mm, height=20 * mm, preserveAspectRatio=True, mask='auto')
                
            # App Title
            c.setFont("Helvetica-Bold", 16)
            c.drawString(65 * mm, height - 28 * mm, "FuldaNexus")
            
        except Exception as e:
            # Fallback text if logo fails
            c.setFont("Helvetica-Bold", 16)
            c.drawString(20 * mm, height - 30 * mm, "FuldaNexus")

        # Event Title
        c.setFont("Helvetica-Bold", 20)
        c.drawString(20 * mm, height - 60 * mm, event_data.get("title", "Event Title"))

        # Event Details
        c.setFont("Helvetica", 14)
        y_position = height - 80 * mm
        line_height = 8 * mm

        details = [
            f"Date: {event_data.get('formatted_date', 'N/A')}",
            f"Location: {event_data.get('location', 'N/A')}",
            f"Price: {event_data.get('price', 'N/A')}",
            f"Attendee: {user_data.get('full_name', 'Guest')}",
            f"Booking ID: {booking_id}"
        ]

        for detail in details:
            c.drawString(20 * mm, y_position, detail)
            y_position -= line_height

        # Generate Static QR Code
        qr_data = "https://example.com/ticket/" + booking_id
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to ReportLab Image
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        qr_image = ImageReader(img_buffer)

        # Draw QR Code
        qr_size = 50 * mm
        c.drawImage(qr_image, width - 20 * mm - qr_size, height - 90 * mm, width=qr_size, height=qr_size)

        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer
