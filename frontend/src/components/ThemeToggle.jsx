import { Moon, Sun } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useDispatch, useSelector } from "react-redux";
import { toggleTheme } from "@/store/slices/themeSlice";

export const ThemeToggle = () => {
  const dispatch = useDispatch();
  const theme = useSelector((state) => state.theme.mode);

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => dispatch(toggleTheme())}
      aria-label="Toggle theme"
      className="rounded-full"
    >
      {theme === "light" ? (
        <Moon className="h-5 w-5" />
      ) : (
        <Sun className="h-5 w-5" />
      )}
    </Button>
  );
};
