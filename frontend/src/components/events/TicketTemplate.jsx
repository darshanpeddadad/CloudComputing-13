import React, { forwardRef } from "react";
import { QRCodeCanvas } from "qrcode.react";
import logo from "../../assets/FuldaNexusLogo.png";

const TicketTemplate = forwardRef(({ event, ticketId, bookingId, qrData, quantity = 1, cartItems = [] }, ref) => {
    if (!event) return null;

    const formattedDate = event.start_date
        ? new Date(event.start_date).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })
        : 'Date N/A';
    const formattedTime = event.start_time ? event.start_time.slice(0, 5) : '';

    return (
        <div ref={ref} style={{
            width: "210mm",
            minHeight: "297mm",
            backgroundColor: "#ffffff",
            padding: "3rem",
            color: "#000000",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            border: "1px solid #e5e7eb",
            fontFamily: "ui-sans-serif, system-ui, sans-serif",
            boxSizing: "border-box"
        }}>

            {/* Header with Logo */}
            <div style={{
                width: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: "3rem",
                paddingBottom: "1.5rem",
                borderBottom: "2px dashed #d1d5db"
            }}>
                <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
                    <img
                        src={logo}
                        alt="FuldaNexus Logo"
                        style={{ width: "60px", height: "60px", objectFit: "contain" }}
                        crossOrigin="anonymous"
                    />
                    <h1 style={{ fontSize: "2.5rem", fontWeight: "800", letterSpacing: "-0.025em", margin: 0 }}>FuldaNexus</h1>
                </div>
                <div style={{ textAlign: "right" }}>
                    <p style={{ fontSize: "1rem", fontFamily: "monospace", color: "#6b7280", letterSpacing: "0.05em", margin: 0, fontWeight: "bold" }}>OFFICIAL TICKET</p>
                    <p style={{ fontSize: "0.75rem", color: "#9ca3af", marginTop: "0.25rem", fontFamily: "monospace", margin: 0 }}>{ticketId || bookingId || "N/A"}</p>
                </div>
            </div>


            <div style={{
                width: "100%",
                display: "block",
                textAlign: "center",
                marginBottom: "3rem"
            }}>
                <h2 style={{
                    fontSize: "3rem",
                    fontWeight: "900",
                    textTransform: "uppercase",
                    letterSpacing: "-0.05em",
                    lineHeight: "1.2",
                    color: "#000000",
                    margin: "0 0 2rem 0",
                    textAlign: "center",
                    wordBreak: "break-word",
                    maxWidth: "100%"
                }}>
                    {event.title}
                </h2>
                <div style={{
                    display: "inline-flex",
                    alignItems: "center",
                    justifyContent: "center",
                    padding: "0.6rem 1.5rem",
                    border: "2px solid #000000",
                    borderRadius: "9999px",
                    fontSize: "1.25rem",
                    fontWeight: "700",
                    textTransform: "uppercase",
                    letterSpacing: "0.025em",
                    lineHeight: "1",
                    color: "#000000",
                    backgroundColor: "transparent"
                }}>
                    <span style={{ transform: "translateY(-0.50rem)", display: "block" }}>
                        {event.category?.name || "Event Ticket"}
                    </span>
                </div>
            </div>

            {/* Content Area - 2x2 Grid */}
            <div style={{
                width: "100%",
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "2rem",
                marginBottom: "3rem"
            }}>
                {/* 1. Date */}
                <div style={{ padding: "1.5rem", backgroundColor: "#f9fafb", borderRadius: "1rem", border: "1px solid #f3f4f6", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                    <p style={{ fontSize: "0.875rem", textTransform: "uppercase", fontWeight: "700", color: "#9ca3af", marginBottom: "0.5rem", letterSpacing: "0.05em" }}>Date</p>
                    <p style={{ fontSize: "1.75rem", fontWeight: "700", color: "#000000", margin: 0, lineHeight: "1.1" }}>{formattedDate}</p>
                    <p style={{ fontSize: "1.125rem", color: "#4b5563", fontWeight: "500", marginTop: "0.25rem", margin: 0 }}>{formattedTime}</p>
                </div>

                {/* 2. Location */}
                <div style={{ padding: "1.5rem", backgroundColor: "#f9fafb", borderRadius: "1rem", border: "1px solid #f3f4f6", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                    <p style={{ fontSize: "0.875rem", textTransform: "uppercase", fontWeight: "700", color: "#9ca3af", marginBottom: "0.5rem", letterSpacing: "0.05em" }}>Location</p>
                    <p style={{ fontSize: "1.5rem", fontWeight: "700", lineHeight: "1.25", color: "#000000", margin: 0, wordBreak: "break-word" }}>{event.location}</p>
                </div>

                {/* 3. Reference */}
                <div style={{ padding: "1.5rem", backgroundColor: "#f9fafb", borderRadius: "1rem", border: "1px solid #f3f4f6", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                    <p style={{ fontSize: "0.875rem", textTransform: "uppercase", fontWeight: "700", color: "#9ca3af", marginBottom: "0.5rem", letterSpacing: "0.05em" }}>Reference</p>
                    <p style={{ fontSize: "1rem", fontFamily: "monospace", letterSpacing: "-0.025em", wordBreak: "break-all", color: "#000000", margin: 0, lineHeight: "1.2" }}>{ticketId || "PENDING"}</p>
                </div>

                {/* 4. Tickets */}
                <div style={{ padding: "1.5rem", backgroundColor: "#f9fafb", borderRadius: "1rem", border: "1px solid #f3f4f6", display: "flex", flexDirection: "column", justifyContent: "center" }}>
                    <p style={{ fontSize: "0.875rem", textTransform: "uppercase", fontWeight: "700", color: "#9ca3af", marginBottom: "0.5rem", letterSpacing: "0.05em" }}>Tickets</p>
                    {cartItems.length > 0 ? (
                        cartItems.map(item => (
                            <div key={item.ticket.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.25rem" }}>
                                <span style={{ fontSize: "1rem", fontWeight: "600", color: "#000000" }}>{item.ticket.name}</span>
                                <span style={{ fontSize: "1rem", fontWeight: "700", color: "#000000", marginLeft: "1rem" }}>×{item.quantity}</span>
                            </div>
                        ))
                    ) : (
                        <p style={{ fontSize: "1.75rem", fontWeight: "700", color: "#000000", margin: 0 }}>{quantity} Person{quantity > 1 ? 's' : ''}</p>
                    )}
                </div>
            </div>

            {/* Large QR Code Area */}
            <div style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "2rem",
                border: "4px solid #000000",
                borderRadius: "2rem",
                backgroundColor: "#ffffff",
                marginBottom: "3rem"
            }}>
                <QRCodeCanvas value={qrData} size={250} level="Q" />
                <p style={{ marginTop: "1rem", fontFamily: "monospace", fontSize: "1rem", color: "#6b7280", letterSpacing: "0.5em", textTransform: "uppercase", fontWeight: "700" }}>Scan for Entry</p>
            </div>

            {/* Footer */}
            <div style={{
                marginTop: "auto",
                width: "100%",
                textAlign: "center",
                borderTop: "1px solid #e5e7eb",
                paddingTop: "2rem",
                paddingBottom: "2rem",
                color: "#9ca3af",
                fontSize: "0.875rem"
            }}>
                <p style={{ margin: 0 }}>&copy; {new Date().getFullYear()} FuldaNexus. All rights reserved.</p>
                <p style={{ margin: "0.5rem 0 0 0" }}>This ticket is non-transferable unless verified through the app.</p>
            </div>

        </div>
    );
});

export default TicketTemplate;
