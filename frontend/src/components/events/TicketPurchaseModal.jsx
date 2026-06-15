import React, { useState, useRef } from "react";
import { QRCodeCanvas } from "qrcode.react";
import { X, Loader2 } from "lucide-react";
import html2canvas from "html2canvas";
import jsPDF from "jspdf";
import logo from "../../assets/FuldaNexusLogo.png";
import TicketTemplate from "./TicketTemplate";

const TicketPurchaseModal = ({ isOpen, onClose, event, ticketId, quantity = 1, cartItems = [] }) => {
    const [isProcessing, setIsProcessing] = useState(false);
    const ticketRef = useRef(null);
    const ticketRefHidden = useRef(null);

    const bookingId = React.useMemo(() => {
        if (!event) return null;
        const storageKey = `booking_id_${event.id}`;
        const stored = localStorage.getItem(storageKey);
        if (stored) return stored;

        const newId = `BK-${event.id.substring(0, 8).toUpperCase()}-${Date.now()}`;
        localStorage.setItem(storageKey, newId);
        return newId;
    }, [event?.id]);

    const stableQrData = React.useMemo(() => {
        if (!event || !bookingId) return "";
        return JSON.stringify({
            eventId: event.id,
            bookingId: bookingId,
            ticketId: ticketId
        });
    }, [event?.id, bookingId, ticketId]);


    if (!isOpen || !event) return null;

    const formattedDate = event.start_date
        ? new Date(event.start_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
        : 'Date N/A';
    const formattedTime = event.start_time ? event.start_time.slice(0, 5) : '';
    const formattedDateTime = formattedTime ? `${formattedDate} at ${formattedTime}` : formattedDate;

    const handleDownload = async () => {

        const elementToCapture = ticketRefHidden.current;
        if (!elementToCapture) {
            return;
        }

        setIsProcessing(true);

        try {
            await new Promise(resolve => setTimeout(resolve, 500));

            const canvas = await html2canvas(elementToCapture, {
                scale: 1,
                useCORS: true,
                allowTaint: true,
                backgroundColor: "#ffffff",
                windowWidth: 1000,
                windowHeight: 1414,
                logging: false,
                onclone: (clonedDoc) => {


                    const images = clonedDoc.getElementsByTagName("img");
                    for (let img of images) {
                        img.loading = "eager";
                    }

                    const styles = clonedDoc.getElementsByTagName("style");
                    const links = clonedDoc.querySelectorAll("link[rel='stylesheet']");

                    Array.from(styles).forEach(style => style.remove());
                    Array.from(links).forEach(link => link.remove());
                }
            });

            const imgData = canvas.toDataURL("image/jpeg", 0.92);

            const pdf = new jsPDF({
                orientation: "p",
                unit: "mm",
                format: "a4",
                compress: true
            });
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

            pdf.addImage(imgData, "JPEG", 0, 0, pdfWidth, pdfHeight, undefined, "FAST");
            pdf.save(`ticket-${event.title.replace(/\s+/g, '-').toLowerCase()}.pdf`);


        } catch (error) {
            console.error("Failed to generate PDF", error);
            alert(`Failed to download ticket: ${error.message}`);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <>
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
                <div className="bg-white rounded-xl shadow-lg w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
                    <div className="flex items-center justify-between p-4 border-b border-gray-200">
                        <h2 className="text-lg font-semibold text-gray-900">Ticket Details</h2>
                        <button
                            onClick={onClose}
                            className="p-1 rounded-full hover:bg-gray-100 text-gray-600 hover:text-gray-900 transition"
                            disabled={isProcessing}
                        >
                            <X size={20} />
                        </button>
                    </div>

                    <div className="p-6 flex flex-col items-center bg-white text-black">
                        <div className="p-4 rounded-xl border-2 border-dashed mb-6 border-gray-200 bg-white">
                            <QRCodeCanvas value={stableQrData} size={180} level="H" />
                        </div>

                        <div className="w-full space-y-4 text-left">
                            <div>
                                <p className="text-xs uppercase font-medium text-gray-500">Event</p>
                                <p className="font-bold text-gray-900">{event.title}</p>
                            </div>

                            <div>
                                <p className="text-xs uppercase font-medium text-gray-500">Date & Time</p>
                                <p className="font-semibold text-gray-900">{formattedDateTime}</p>
                            </div>

                            <div>
                                <p className="text-xs uppercase font-medium text-gray-500">Location</p>
                                <p className="font-semibold text-gray-900">{event.location}</p>
                            </div>

                            <div>
                                <p className="text-xs uppercase font-medium text-gray-500">Ticket Reference</p>
                                <p className="font-mono text-sm text-gray-900">{ticketId || bookingId}</p>
                            </div>
                        </div>
                    </div>

                    <div className="p-4 border-t flex gap-3">
                        <button
                            onClick={handleDownload}
                            disabled={isProcessing}
                            className="flex-1 bg-black text-white py-2.5 rounded-lg font-semibold hover:opacity-90 transition cursor-pointer flex items-center justify-center gap-2"
                        >
                            {isProcessing ? (
                                <>
                                    <Loader2 className="animate-spin" size={18} />
                                    Processing...
                                </>
                            ) : (
                                "Download Ticket (PDF)"
                            )}
                        </button>
                        <button
                            onClick={onClose}
                            disabled={isProcessing}
                            className="flex-1 bg-white border border-gray-300 text-gray-700 py-2.5 rounded-lg font-semibold hover:bg-gray-50 transition"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>

            <div style={{
                position: "fixed",
                top: "-9999px",
                left: "-9999px",
                visibility: "visible",
                "--background": "#ffffff",
                "--foreground": "#000000",
                "--card": "#ffffff",
                "--card-foreground": "#000000",
                "--popover": "#ffffff",
                "--popover-foreground": "#000000",
                "--primary": "#000000",
                "--primary-foreground": "#ffffff",
                "--secondary": "#f3f4f6",
                "--secondary-foreground": "#111827",
                "--muted": "#f3f4f6",
                "--muted-foreground": "#6b7280",
                "--accent": "#f3f4f6",
                "--accent-foreground": "#111827",
                "--destructive": "#ef4444",
                "--destructive-foreground": "#ffffff",
                "--border": "#e5e7eb",
                "--input": "#e5e7eb",
                "--ring": "#000000",
                "--radius": "0.5rem",
                "--chart-1": "#000000",
                "--chart-2": "#000000",
                "--chart-3": "#000000",
                "--chart-4": "#000000",
                "--chart-5": "#000000",
                "--sidebar": "#ffffff",
                "--sidebar-foreground": "#000000",
                "--sidebar-primary": "#000000",
                "--sidebar-primary-foreground": "#ffffff",
                "--sidebar-accent": "#f3f4f6",
                "--sidebar-accent-foreground": "#111827",
                "--sidebar-border": "#e5e7eb",
                "--sidebar-ring": "#000000",
                "--gradient-brand": "linear-gradient(135deg, #000000, #333333)"
            }}>
                            <TicketTemplate
                    ref={ticketRefHidden}
                    event={event}
                    ticketId={ticketId}
                    bookingId={bookingId}
                    qrData={stableQrData}
                    quantity={quantity}
                    cartItems={cartItems}
                />
            </div>
        </>
    );
};

export default TicketPurchaseModal;
