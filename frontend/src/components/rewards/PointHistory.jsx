import React from "react";
import { ArrowUpCircle, ArrowDownCircle, Calendar, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

/**
 * Format date for display
 */
const formatDate = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
};

/**
 * Format time for display
 */
const formatTime = (dateString) => {
  const date = new Date(dateString);
  return date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
  });
};

/**
 * Get reason display text
 */
const getReasonDisplay = (reason) => {
  const reasonMap = {
    event_attendance: "Event Attendance",
    redemption_discount: "Points Redeemed",
    bonus: "Bonus Points",
    referral: "Referral Bonus",
    adjustment: "Admin Adjustment",
  };
  return reasonMap[reason] || reason;
};

/**
 * PointHistory component - Displays transaction history
 */
const PointHistory = ({
  transactions,
  loading = false,
  emptyMessage = "No transactions yet",
}) => {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="text-center py-12">
        <Clock className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border">
      <Table>
        <TableHeader>
          <TableRow className="bg-muted/50">
            <TableHead className="w-12"></TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-center">Date</TableHead>
            <TableHead className="text-right">Points</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {transactions.map((transaction) => {
            const isPositive = transaction.points_delta > 0;
            return (
              <TableRow key={transaction.id} className="hover:bg-muted/30">
                <TableCell>
                  {isPositive ? (
                    <ArrowUpCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <ArrowDownCircle className="w-5 h-5 text-red-500" />
                  )}
                </TableCell>
                <TableCell>
                  <div className="flex flex-col">
                    <span className="font-medium">
                      {transaction.description ||
                        getReasonDisplay(transaction.reason)}
                    </span>
                    {transaction.event_id && (
                      <span className="text-xs text-muted-foreground">
                        Event ID: {transaction.event_id.slice(0, 8)}...
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "px-2 py-1 rounded-full text-xs font-medium",
                      isPositive
                        ? "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400"
                        : "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
                    )}
                  >
                    {getReasonDisplay(transaction.reason)}
                  </span>
                </TableCell>
                <TableCell className="text-center">
                  <div className="flex flex-col items-center">
                    <span className="text-sm">
                      {formatDate(transaction.created_at)}
                    </span>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(transaction.created_at)}
                    </span>
                  </div>
                </TableCell>
                <TableCell className="text-right">
                  <span
                    className={cn(
                      "font-bold text-lg",
                      isPositive
                        ? "text-green-600 dark:text-green-400"
                        : "text-red-600 dark:text-red-400",
                    )}
                  >
                    {isPositive ? "+" : ""}
                    {transaction.points_delta.toLocaleString()}
                  </span>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
};

export default PointHistory;
