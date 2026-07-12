import jsPDF from "jspdf"

// jsPDF's built-in fonts don't include the ₹ glyph (WinAnsi encoding only) —
// it would render as a blank box, so PDFs use "Rs." instead. The on-screen
// UI keeps ₹ everywhere else; this swap is only for the generated file.
function rupeesToRs(text) {
  return String(text).replace(/₹/g, "Rs. ")
}

/**
 * Renders a simple label/value invoice as a real PDF and triggers a browser
 * download — replaces the old window.open()+print() approach, which only
 * opened a print dialog instead of actually saving a file.
 *
 * @param {string} title - document heading, e.g. "Cyber Panchayat — Booking Invoice"
 * @param {string} invoiceNumber
 * @param {string} issuedAt
 * @param {Array<[string, string, {divider?: boolean, bold?: boolean}?]>} rows
 * @param {string} filename
 */
export function downloadInvoicePdf({ title, invoiceNumber, issuedAt, rows, filename }) {
  const doc = new jsPDF({ unit: "mm", format: "a4" })
  const marginL = 18
  const marginR = 192
  let y = 22

  doc.setFont("helvetica", "bold")
  doc.setFontSize(16)
  doc.text(title, marginL, y)

  y += 7
  doc.setFont("helvetica", "normal")
  doc.setFontSize(10)
  doc.setTextColor(100)
  doc.text(`Invoice ${invoiceNumber}  •  Issued ${issuedAt}`, marginL, y)
  doc.setTextColor(20)

  y += 6
  doc.setDrawColor(220)
  doc.line(marginL, y, marginR, y)
  y += 10

  rows.forEach(([label, value, opts = {}]) => {
    if (opts.divider) {
      doc.setDrawColor(220)
      doc.line(marginL, y - 5, marginR, y - 5)
    }
    doc.setFont("helvetica", opts.bold ? "bold" : "normal")
    doc.setFontSize(opts.bold ? 12 : 10.5)
    doc.text(label, marginL, y)
    doc.text(rupeesToRs(value), marginR, y, { align: "right" })
    y += 8
  })

  doc.save(filename)
}
