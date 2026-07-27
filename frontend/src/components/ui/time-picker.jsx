import React, { useState, useRef, useEffect } from "react";
import { Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export function TimePicker({ value, onChange, placeholder = "Pick time" }) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedHour, setSelectedHour] = useState(
    value ? value.split(":")[0] : "12"
  );
  const [selectedMinute, setSelectedMinute] = useState(
    value ? value.split(":")[1] : "00"
  );

  const hourRef = useRef(null);
  const minuteRef = useRef(null);

  const hours = Array.from({ length: 24 }, (_, i) =>
    String(i).padStart(2, "0")
  );
  const minutes = Array.from({ length: 60 }, (_, i) =>
    String(i).padStart(2, "0")
  );

  useEffect(() => {
    if (value) {
      const [h, m] = value.split(":");
      setSelectedHour(h);
      setSelectedMinute(m);
    }
  }, [value]);

  const handleConfirm = () => {
    const timeString = `${selectedHour}:${selectedMinute}`;
    onChange(timeString);
    setIsOpen(false);
  };

  const scrollToSelected = (ref, value, items) => {
    if (ref.current) {
      const index = items.indexOf(value);
      const itemHeight = 36;
      ref.current.scrollTop = index * itemHeight - 72;
    }
  };

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => {
        scrollToSelected(hourRef, selectedHour, hours);
        scrollToSelected(minuteRef, selectedMinute, minutes);
      }, 10);
    }
  }, [isOpen]);

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            "w-full justify-between text-left font-normal",
            !value && "text-muted-foreground"
          )}
        >
          {value || <span>{placeholder}</span>}
          <Clock className="h-4 w-4 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <div className="flex flex-col p-4">
          <div className="flex gap-3 mb-3">
            <div className="flex flex-col items-center">
              <div className="text-xs font-medium text-center mb-2 text-muted-foreground">
                Hour
              </div>
              <div
                ref={hourRef}
                className="h-[180px] w-[70px] overflow-y-auto border rounded-md bg-background"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'hsl(var(--muted)) transparent'
                }}
              >
                {hours.map((h) => (
                  <button
                    key={h}
                    type="button"
                    onClick={() => setSelectedHour(h)}
                    className={cn(
                      "w-full px-2 py-2 text-sm hover:bg-accent transition-colors text-center",
                      selectedHour === h &&
                        "bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
                    )}
                  >
                    {h}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col items-center">
              <div className="text-xs font-medium text-center mb-2 text-muted-foreground">
                Minute
              </div>
              <div
                ref={minuteRef}
                className="h-[180px] w-[70px] overflow-y-auto border rounded-md bg-background"
                style={{
                  scrollbarWidth: 'thin',
                  scrollbarColor: 'hsl(var(--muted)) transparent'
                }}
              >
                {minutes.map((m) => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setSelectedMinute(m)}
                    className={cn(
                      "w-full px-2 py-2 text-sm hover:bg-accent transition-colors text-center",
                      selectedMinute === m &&
                        "bg-primary text-primary-foreground hover:bg-primary/90 font-medium"
                    )}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <Button onClick={handleConfirm} size="sm" className="w-full">
            Confirm
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
