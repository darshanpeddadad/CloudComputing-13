import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";

import { TagInput } from "@/components/TagInput";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useSelector, useDispatch } from "react-redux";
import { registerUser, clearError, resetRegistration } from "@/store/slices/authSlice";
import { Loader2, ChevronDownIcon, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import { cn } from "@/lib/utils";
import { Calendar } from "@/components/ui/calendar";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Logo } from "@/components/Logo";

export default function Register() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { loading, error, isRegistered, isAuthenticated } = useSelector((state) => state.auth);

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [isCalendarOpen, setIsCalendarOpen] = useState(false);

  const [formData, setFormData] = useState({
    first_names: "",
    last_name: "",
    email: "",
    dob: "",
    password: "",
    confirm_password: "",
    interests: [],
  });

  const [errors, setErrors] = useState({});

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/");
    }
    if (isRegistered) {
      toast.success("You're all set! Please log in to access your account.");
      navigate("/login");
    }
  }, [isRegistered, isAuthenticated, navigate]);

  useEffect(() => {
    return () => {
      dispatch(clearError());
      dispatch(resetRegistration());
    };
  }, [dispatch]);

  // client-side form validation
  const validateForm = () => {
    const newErrors = {};

    if (!formData.first_names.trim()) {
      newErrors.first_names = "First name is required";
    }

    if (!formData.last_name.trim()) {
      newErrors.last_name = "Last name is required";
    }

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    } else if (!formData.email.endsWith("hs-fulda.de")) {
      newErrors.email = "Email must end with hs-fulda.de";
    }

    if (!formData.dob) {
      newErrors.dob = "Date of birth is required";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 8) {
      newErrors.password = "Password must be at least 8 characters";
    }

    if (!formData.confirm_password) {
      newErrors.confirm_password = "Please confirm your password";
    } else if (formData.password !== formData.confirm_password) {
      newErrors.confirm_password = "Passwords do not match";
    }

    if (formData.interests.length === 0) {
      newErrors.interests = "Please add at least one interest";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (validateForm()) {
      await dispatch(registerUser(formData));
    }
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    // Clear error for this field when user starts typing
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  return (
    <div className="min-h-screen bg-background">


      <main className="container mx-auto px-4 py-8 md:py-12">
        <div className="flex items-center justify-center">
          <Card className="w-full max-w-2xl shadow-lg">
            <div className="flex justify-center pt-6">
              <Logo className="text-2xl md:text-4xl" />
            </div>
            <CardHeader className="space-y-1 text-center">
              <CardTitle className="text-xl md:text-2xl font-bold tracking-tight">
                Create an account
              </CardTitle>
              <CardDescription className="text-base">
                Enter your details to register for FuldaNexus
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="first_names">First Name(s) *</Label>
                    <Input
                      id="first_names"
                      type="text"
                      value={formData.first_names}
                      onChange={(e) =>
                        handleChange("first_names", e.target.value)
                      }
                      aria-invalid={!!errors.first_names}
                      aria-describedby={
                        errors.first_names ? "first_names-error" : undefined
                      }
                    />
                    {errors.first_names && (
                      <p
                        id="first_names-error"
                        className="text-sm text-destructive"
                      >
                        {errors.first_names}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="last_name">Last Name *</Label>
                    <Input
                      id="last_name"
                      type="text"
                      value={formData.last_name}
                      onChange={(e) =>
                        handleChange("last_name", e.target.value)
                      }
                      aria-invalid={!!errors.last_name}
                      aria-describedby={
                        errors.last_name ? "last_name-error" : undefined
                      }
                    />
                    {errors.last_name && (
                      <p
                        id="last_name-error"
                        className="text-sm text-destructive"
                      >
                        {errors.last_name}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email *</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="student@hs-fulda.de"
                    value={formData.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? "email-error" : undefined}
                  />
                  {errors.email && (
                    <p id="email-error" className="text-sm text-destructive">
                      {errors.email}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="dob">Date of Birth *</Label>
                  <Popover open={isCalendarOpen} onOpenChange={setIsCalendarOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant={"outline"}
                        className={cn(
                          "w-full justify-between text-left font-normal",
                          !formData.dob && "text-muted-foreground"
                        )}
                      >
                        {formData.dob ? (
                          format(new Date(formData.dob), "PPP")
                        ) : (
                          <span>Pick a date</span>
                        )}
                        <ChevronDownIcon className="h-4 w-4 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0" align="start">
                      <Calendar
                        mode="single"
                        selected={formData.dob ? new Date(formData.dob) : undefined}
                        onSelect={(date) => {
                          handleChange("dob", date ? format(date, "yyyy-MM-dd") : "");
                          setIsCalendarOpen(false);
                        }}
                        initialFocus
                        captionLayout="dropdown"
                        fromYear={1900}
                        toYear={new Date().getFullYear()}
                        disabled={(date) =>
                          date > new Date() || date < new Date("1900-01-01")
                        }
                      />
                    </PopoverContent>
                  </Popover>
                  {errors.dob && (
                    <p id="dob-error" className="text-sm text-destructive">
                      {errors.dob}
                    </p>
                  )}
                </div>

                <div className="grid md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="password">Password *</Label>
                    <div className="relative">
                      <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={formData.password}
                        onChange={(e) => handleChange("password", e.target.value)}
                        aria-invalid={!!errors.password}
                        aria-describedby={
                          errors.password ? "password-error" : undefined
                        }
                        className="pr-10"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? (
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="sr-only">
                          {showPassword ? "Hide password" : "Show password"}
                        </span>
                      </Button>
                    </div>
                    {errors.password && (
                      <p
                        id="password-error"
                        className="text-sm text-destructive"
                      >
                        {errors.password}
                      </p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirm_password">Confirm Password *</Label>
                    <div className="relative">
                      <Input
                        id="confirm_password"
                        type={showConfirmPassword ? "text" : "password"}
                        value={formData.confirm_password}
                        onChange={(e) =>
                          handleChange("confirm_password", e.target.value)
                        }
                        aria-invalid={!!errors.confirm_password}
                        aria-describedby={
                          errors.confirm_password
                            ? "confirm_password-error"
                            : undefined
                        }
                        className="pr-10"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? (
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                        ) : (
                          <Eye className="h-4 w-4 text-muted-foreground" />
                        )}
                        <span className="sr-only">
                          {showConfirmPassword ? "Hide password" : "Show password"}
                        </span>
                      </Button>
                    </div>
                    {errors.confirm_password && (
                      <p
                        id="confirm_password-error"
                        className="text-sm text-destructive"
                      >
                        {errors.confirm_password}
                      </p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="interests">Interests *</Label>
                  <TagInput
                    value={formData.interests}
                    onChange={(tags) => handleChange("interests", tags)}
                    placeholder="Type an interest and press Enter"
                  />
                  {errors.interests && (
                    <p className="text-sm text-destructive">
                      {errors.interests}
                    </p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full"
                  disabled={loading}
                  size="lg"
                >
                  {loading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Creating account...
                    </>
                  ) : (
                    "Create account"
                  )}
                </Button>

                <p className="text-center text-sm text-muted-foreground">
                  Already have an account?{" "}
                  <Link
                    to="/login"
                    className="text-primary hover:text-accent transition-colors font-medium"
                  >
                    Log in
                  </Link>
                </p>
              </form>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
