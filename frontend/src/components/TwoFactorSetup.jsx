import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Copy, CheckCircle } from "lucide-react";
import authApiService from "@/services/authApiService";
import { toast } from "sonner";

export default function TwoFactorSetup({ isOpen, onClose, onStatusChange }) {
    // Track setup stage: "loading", "scan", "backup", etc.
    const [step, setStep] = useState("loading");
    const [qrCode, setQrCode] = useState(null);
    const [secret, setSecret] = useState(null);
    const [code, setCode] = useState("");
    const [backupCodes, setBackupCodes] = useState([]);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            initSetup();
        } else {
             // Reset state when closed
             setStep("loading");
             setCode("");
             setError(null);
        }
    }, [isOpen]);

    const initSetup = async () => {
        try {
            setStep("loading");
            const data = await authApiService.enable2FA();
            setQrCode(data.data.qr_code);
            setSecret(data.data.secret);
            setStep("scan");
        } catch (err) {
            setError("Failed to initialize 2FA setup. Please try again.");
            toast.error("Failed to start 2FA setup");
            onClose();
        }
    };

    const handleVerify = async () => {
        if (!code || code.length !== 6) {
            setError("Please enter a valid 6-digit code.");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const data = await authApiService.verify2FA(code);
            setBackupCodes(data.data.backup_codes);
            setStep("backup");
            toast.success("2FA Enabled Successfully!");
            if (onStatusChange) onStatusChange(true);
        } catch (err) {
            setError("Invalid code. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    const handleCopyBackupCodes = () => {
        const text = backupCodes.join("\n");
        navigator.clipboard.writeText(text);
        toast.success("Backup codes copied to clipboard");
    };

    const handleClose = () => {
        onClose();
    };

    return (
        <Dialog open={isOpen} onOpenChange={handleClose}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Enable Two-Factor Authentication</DialogTitle>
                    <DialogDescription>
                        Secure your account with Google Authenticator.
                    </DialogDescription>
                </DialogHeader>

                <div className="py-4">
                    {step === "loading" && (
                        <div className="flex justify-center py-8">
                            <Loader2 className="h-8 w-8 animate-spin text-primary" />
                        </div>
                    )}

                    {step === "scan" && (
                        <div className="space-y-4">
                            <div className="flex flex-col items-center justify-center space-y-4">
                                <div className="p-2 bg-white rounded-lg border">
                                    {qrCode && (
                                        <img 
                                            src={`data:image/png;base64,${qrCode}`} 
                                            alt="2FA QR Code" 
                                            className="w-48 h-48"
                                        />
                                    )}
                                </div>
                                <div className="text-center text-sm text-muted-foreground">
                                    <p>Scan this QR code with your authenticator app.</p>
                                    <p className="font-mono mt-2 text-xs">Secret: {secret}</p>
                                </div>
                            </div>

                            <div className="space-y-2">
                                <Label htmlFor="otp">Enter 6-digit code</Label>
                                <Input
                                    id="otp"
                                    value={code}
                                    onChange={(e) => setCode(e.target.value)}
                                    placeholder="123456"
                                    maxLength={6}
                                    className="text-center text-lg tracking-widest"
                                />
                            </div>

                            {error && (
                                <Alert variant="destructive">
                                    <AlertDescription>{error}</AlertDescription>
                                </Alert>
                            )}
                        </div>
                    )}

                    {step === "backup" && (
                        <div className="space-y-4">
                            <Alert className="border-green-500/50 bg-green-500/10 text-green-700 dark:text-green-400">
                                <CheckCircle className="h-4 w-4" />
                                <AlertDescription>
                                    Two-factor authentication is now enabled.
                                </AlertDescription>
                            </Alert>

                            <div className="space-y-2">
                                <Label>Save your backup codes</Label>
                                <p className="text-sm text-muted-foreground">
                                    If you lose your device, you can use these codes to recover access to your account. Keep them safe.
                                </p>
                                <div className="bg-muted p-4 rounded-md font-mono text-sm flex flex-wrap gap-2 justify-center max-h-60 overflow-y-auto">
                                    {backupCodes.map((c, i) => (
                                        <span key={i} className="bg-background p-1 px-2 rounded border">{c}</span>
                                    ))}
                                </div>
                            </div>
                            
                            <Button variant="outline" size="sm" onClick={handleCopyBackupCodes} className="w-full">
                                <Copy className="mr-2 h-4 w-4" /> Copy All Codes
                            </Button>
                        </div>
                    )}
                </div>

                <DialogFooter className="sm:justify-end">
                     {step === "scan" && (
                        <Button onClick={handleVerify} disabled={loading || code.length !== 6} className="w-full sm:w-auto">
                            {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                            Verify & Enable
                        </Button>
                    )}
                    {step === "backup" && (
                        <Button onClick={handleClose} className="w-full sm:w-auto">
                            Done
                        </Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
