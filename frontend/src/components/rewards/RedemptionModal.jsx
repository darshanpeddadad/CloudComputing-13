import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { Gift, AlertCircle, CheckCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  previewRedemption,
  redeemPoints,
  clearRedemptionPreview,
  fetchMyProfile,
} from "@/store/slices/rewardSlice";

/**
 * RedemptionModal component - Handles point redemption flow
 */
const RedemptionModal = ({
  isOpen,
  onClose,
  currentPoints = 0,
  redemptionRate,
}) => {
  const dispatch = useDispatch();
  const { redemptionPreview, redemptionLoading, redemptionError } = useSelector(
    (state) => state.rewards,
  );

  const [pointsInput, setPointsInput] = useState("");
  const [redeemSuccess, setRedeemSuccess] = useState(false);

  // Reset state when modal opens/closes
  useEffect(() => {
    if (isOpen) {
      setPointsInput("");
      setRedeemSuccess(false);
      dispatch(clearRedemptionPreview());
    }
  }, [isOpen, dispatch]);

  const minPoints = redemptionRate?.min_redemption_points || 100;
  const rate = redemptionRate?.points_to_currency_rate || 0.01;
  const currency = redemptionRate?.currency || "EUR";

  const handlePreview = () => {
    const points = parseInt(pointsInput, 10);
    if (points && points >= minPoints) {
      dispatch(previewRedemption({ pointsToRedeem: points }));
    }
  };

  const handleRedeem = async () => {
    const points = parseInt(pointsInput, 10);
    if (points && redemptionPreview?.is_valid) {
      const result = await dispatch(redeemPoints({ pointsToRedeem: points }));
      if (!result.error) {
        setRedeemSuccess(true);
        dispatch(fetchMyProfile()); // Refresh profile
        setTimeout(() => {
          onClose();
        }, 2000);
      }
    }
  };

  const handlePointsChange = (e) => {
    const value = e.target.value.replace(/[^0-9]/g, "");
    setPointsInput(value);
    dispatch(clearRedemptionPreview());
  };

  const quickAmounts = [100, 250, 500, 1000].filter(
    (amt) => amt <= currentPoints,
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Gift className="w-5 h-5 text-primary" />
            Redeem Points
          </DialogTitle>
          <DialogDescription>
            Convert your points into discounts for future events.
          </DialogDescription>
        </DialogHeader>

        {redeemSuccess ? (
          <div className="py-8 text-center">
            <CheckCircle className="w-16 h-16 mx-auto text-green-500 mb-4" />
            <h3 className="text-lg font-bold text-green-600">
              Redemption Successful!
            </h3>
            <p className="text-muted-foreground mt-2">
              Your discount code has been applied to your account.
            </p>
          </div>
        ) : (
          <>
            <div className="space-y-4 py-4">
              {/* Current Balance */}
              <div className="bg-muted/50 p-4 rounded-lg">
                <div className="flex justify-between items-center">
                  <span className="text-muted-foreground">
                    Available Points
                  </span>
                  <span className="text-2xl font-bold text-primary">
                    {currentPoints.toLocaleString()}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  1 point = {currency} {rate.toFixed(2)}
                </p>
              </div>

              {/* Points Input */}
              <div className="space-y-2">
                <Label htmlFor="points">Points to Redeem</Label>
                <Input
                  id="points"
                  type="text"
                  placeholder={`Minimum ${minPoints} points`}
                  value={pointsInput}
                  onChange={handlePointsChange}
                  className="text-lg"
                />
                {pointsInput && parseInt(pointsInput) < minPoints && (
                  <p className="text-xs text-destructive">
                    Minimum redemption is {minPoints} points
                  </p>
                )}
              </div>

              {/* Quick Amount Buttons */}
              {quickAmounts.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {quickAmounts.map((amount) => (
                    <Button
                      key={amount}
                      variant="outline"
                      size="sm"
                      onClick={() => setPointsInput(amount.toString())}
                      className="text-xs"
                    >
                      {amount}
                    </Button>
                  ))}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setPointsInput(currentPoints.toString())}
                    className="text-xs"
                  >
                    Max
                  </Button>
                </div>
              )}

              {/* Preview Button */}
              {!redemptionPreview && (
                <Button
                  onClick={handlePreview}
                  disabled={
                    !pointsInput ||
                    parseInt(pointsInput) < minPoints ||
                    redemptionLoading
                  }
                  className="w-full"
                  variant="outline"
                >
                  {redemptionLoading ? "Calculating..." : "Preview Discount"}
                </Button>
              )}

              {/* Preview Result */}
              {redemptionPreview && (
                <div className="space-y-3">
                  <div className="bg-primary/5 p-4 rounded-lg border border-primary/20">
                    <h4 className="font-medium mb-2">Redemption Preview</h4>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span>Points to redeem:</span>
                        <span className="font-medium">
                          {redemptionPreview.points_to_redeem.toLocaleString()}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Discount amount:</span>
                        <span className="font-bold text-green-600">
                          {redemptionPreview.currency}{" "}
                          {redemptionPreview.discount_amount.toFixed(2)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Balance after:</span>
                        <span>
                          {redemptionPreview.balance_after_redemption.toLocaleString()}{" "}
                          pts
                        </span>
                      </div>
                    </div>
                  </div>

                  {!redemptionPreview.is_valid && (
                    <Alert variant="destructive">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>
                        {redemptionPreview.validation_message}
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}

              {/* Error Display */}
              {redemptionError && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{redemptionError}</AlertDescription>
                </Alert>
              )}
            </div>

            <DialogFooter className="gap-2">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                onClick={handleRedeem}
                disabled={!redemptionPreview?.is_valid || redemptionLoading}
              >
                {redemptionLoading ? "Processing..." : "Confirm Redemption"}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default RedemptionModal;
