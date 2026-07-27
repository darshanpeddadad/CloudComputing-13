import React, { useState, useEffect } from 'react';
import { Ticket, DollarSign, Euro, FileText } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";

const ResellTicketModal = ({ isOpen, onClose, onConfirm, ticket, loading }) => {
    const [askingPrice, setAskingPrice] = useState('');
    const [notes, setNotes] = useState('');
    const [error, setError] = useState('');
    const [quantityToSell, setQuantityToSell] = useState(1);

    // Reset state when modal opens
    useEffect(() => {
        if (isOpen) {
            setAskingPrice('');
            setNotes('');
            setError('');
            setQuantityToSell(1);
        }
    }, [isOpen]);

    if (!ticket) return null;

    const handleSubmit = (e) => {
        e.preventDefault();
        setError('');

        const price = parseFloat(askingPrice);
        if (isNaN(price) || price <= 0) {
            setError('Please enter a valid price greater than 0.');
            return;
        }

        onConfirm({
            askingPrice: price,
            notes,
            currency: ticket?.currency || 'EUR',
            quantityToSell
        });
    };

    const currencyCode = ticket?.currency || 'EUR';
    const isUSD = currencyCode === 'USD' || currencyCode === '$';
    const currencyLabel = isUSD ? 'USD' : (currencyCode === '€' ? 'EUR' : currencyCode);
    const currencySymbol = isUSD ? '$' : (currencyCode === 'EUR' ? '€' : currencyCode);
    const CurrencyIcon = isUSD ? DollarSign : Euro;

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Ticket className="w-5 h-5 text-primary" />
                        Resell Ticket
                    </DialogTitle>
                </DialogHeader>

                <form onSubmit={handleSubmit} className="space-y-6 py-4">
                    <div className="space-y-4">
                        <div className="bg-muted/50 p-4 rounded-lg space-y-2">
                            <p className="text-sm text-muted-foreground">Event</p>
                            <p className="font-semibold text-lg">{ticket.event_name}</p>
                            <div className="flex justify-between text-sm">
                                <span className="text-muted-foreground">Original Price:</span>
                                <span className="font-medium">{ticket.price}{currencySymbol}</span>
                            </div>
                            {ticket.quantity > 1 && (
                                <div className="flex justify-between text-sm pt-2 border-t border-muted-foreground/10">
                                    <span className="text-muted-foreground">Tickets Owned:</span>
                                    <span className="font-bold text-primary">{ticket.quantity}</span>
                                </div>
                            )}
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="price" className="flex items-center gap-2">
                                <CurrencyIcon className="w-4 h-4 text-primary" />
                                Asking Price Per Ticket ({currencyLabel})
                            </Label>
                            <Input
                                id="price"
                                type="number"
                                placeholder="0.00"
                                value={askingPrice}
                                onChange={(e) => setAskingPrice(e.target.value)}
                                min="0"
                                step="0.01"
                                className="border-primary/20 focus-visible:ring-primary/20"
                                required
                            />
                        </div>

                        {ticket.quantity > 1 && (
                            <div className="space-y-2">
                                <Label htmlFor="quantityToSell" className="flex items-center gap-2">
                                    <Ticket className="w-4 h-4 text-primary" />
                                    Tickets to Resell
                                </Label>
                                <select
                                    id="quantityToSell"
                                    value={quantityToSell}
                                    onChange={(e) => setQuantityToSell(parseInt(e.target.value, 10))}
                                    className="flex h-10 w-full rounded-md border border-primary/20 bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/20 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                    required
                                >
                                    {Array.from({ length: ticket.quantity }, (_, i) => i + 1).map(num => (
                                        <option key={num} value={num}>{num}</option>
                                    ))}
                                </select>
                            </div>
                        )}

                        <div className="space-y-2">
                            <Label htmlFor="notes" className="flex items-center gap-2">
                                <FileText className="w-4 h-4 text-primary" />
                                Notes (Optional)
                            </Label>
                            <Textarea
                                id="notes"
                                placeholder="e.g. Great seat, can't make it..."
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                className="border-primary/20 focus-visible:ring-primary/20 min-h-[100px]"
                            />
                        </div>

                        {error && (
                            <p className="text-sm text-red-500 bg-red-50 dark:bg-red-900/10 p-2 rounded border border-red-200 dark:border-red-900/20">
                                {error}
                            </p>
                        )}
                    </div>

                    <DialogFooter className="gap-2 sm:gap-0">
                        <Button
                            type="button"
                            variant="outline"
                            onClick={() => onClose(false)}
                            className="border-primary/20 hover:bg-primary/5"
                            disabled={loading}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            className="bg-primary hover:bg-primary/90"
                            disabled={loading}
                        >
                            {loading ? (
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                            ) : (
                                "Confirm Resale"
                            )}
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
};

export default ResellTicketModal;
