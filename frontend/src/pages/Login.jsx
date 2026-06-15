import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router";

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
import { loginUser, clearError, verify2FALogin, reset2FAState } from "@/store/slices/authSlice";
import { Loader2, Eye, EyeOff, ArrowLeft } from "lucide-react";
import { Logo } from "@/components/Logo";

export default function Login() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { loading, error, isAuthenticated, user, is2FARequired, tempToken } = useSelector(
    (state) => state.auth
  );

  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [errors, setErrors] = useState({});
  const [otp, setOtp] = useState("");
  const [useBackupCode, setUseBackupCode] = useState(false);

  useEffect(() => {
    if (isAuthenticated && user) {
      // Support both user data formats
      const userRoles = user.user?.roles || user.roles;

      if (userRoles && userRoles[0] === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/events");
      }
    }
  }, [isAuthenticated, user, navigate]);

  useEffect(() => {
    return () => {
      dispatch(clearError());
    };
  }, [dispatch]);

  const validateForm = () => {
    const newErrors = {};

    if (!formData.email.trim()) {
      newErrors.email = "Email is required";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (validateForm()) {
      await dispatch(loginUser(formData));
    }
  };

  const handleOTPSubmit = async (e) => {
      e.preventDefault();
      if(!otp || otp.length < 6) {
          setErrors({ otp: "Please enter a valid authentication code"});
          return;
      }
      await dispatch(verify2FALogin({ tempToken, code: otp }));
  };
  
  const handleBackToLogin = (e) => {
      e?.preventDefault();
      dispatch(reset2FAState());
      setOtp("");
      setUseBackupCode(false);
      setErrors({});
  };

  const handleChange = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: "" }));
    }
  };

  return (
    <div className="min-h-screen bg-background">


      <main className="container mx-auto px-4 py-8 md:py-16">
        <div className="flex items-center justify-center">
          <Card className="w-full max-w-md shadow-lg">
            <div className="flex justify-center pt-6">
              <Logo className="text-2xl md:text-4xl" />
            </div>
            <CardHeader className="space-y-1 text-center">
              <CardTitle className="text-xl md:text-2xl font-bold tracking-tight">
                {is2FARequired ? "Two-Factor Authentication" : "Welcome back"}
              </CardTitle>
              <CardDescription className="text-base">
                {is2FARequired 
                    ? (useBackupCode 
                        ? "Enter one of your 8-character backup codes" 
                        : "Enter the 6-digit code from your authenticator app")
                    : "Log in to your FuldaNexus account"}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {is2FARequired ? (
                  // 2FA Code Form
                  <form onSubmit={handleOTPSubmit} className="space-y-5">
                      {error && (
                        <Alert variant="destructive">
                          <AlertDescription>{error}</AlertDescription>
                        </Alert>
                      )}
                      
                      <div className="space-y-2">
                        <Label htmlFor="otp">
                            {useBackupCode ? "Backup Code" : "Authentication Code"}
                        </Label>
                        <Input
                          id="otp"
                          type="text"
                          placeholder={useBackupCode ? "abcdef12" : "123456"}
                          value={otp}
                          onChange={(e) => {
                              setOtp(e.target.value);
                              if(errors.otp) setErrors(prev => ({...prev, otp: ""}));
                          }}
                          maxLength={32}
                          className="text-center text-lg tracking-widest"
                          autoComplete="one-time-code"
                        />
                         {errors.otp && (
                            <p className="text-sm text-destructive">{errors.otp}</p>
                         )}
                         <div className="text-right">
                             <Button 
                                type="button" 
                                variant="link" 
                                className="p-0 h-auto text-xs text-muted-foreground hover:text-primary"
                                onClick={() => {
                                    setUseBackupCode(!useBackupCode);
                                    setOtp("");
                                    setErrors({});
                                }}
                             >
                                {useBackupCode ? "Use Authenticator App" : "Use Backup Code"}
                             </Button>
                         </div>
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
                            Verifying...
                          </>
                        ) : (
                          "Verify Code"
                        )}
                      </Button>
                      
                       <Button
                        type="button"
                        variant="ghost"
                        className="w-full"
                        onClick={handleBackToLogin}
                        disabled={loading}
                      >
                        <ArrowLeft className="mr-2 h-4 w-4" />
                        Back to Login
                      </Button>
                  </form>
              ) : (
                  // Standard Login Form
                  <form onSubmit={handleSubmit} className="space-y-5">
                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="student@hs-fulda.de"
                    value={formData.email}
                    onChange={(e) => handleChange("email", e.target.value)}
                    aria-invalid={!!errors.email}
                    aria-describedby={errors.email ? "email-error" : undefined}
                    autoComplete="email"
                  />
                  {errors.email && (
                    <p id="email-error" className="text-sm text-destructive">
                      {errors.email}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <Label htmlFor="password">Password</Label>
                    <Link
                      to="#"
                      className="text-sm text-primary hover:text-accent transition-colors"
                      onClick={(e) => e.preventDefault()}
                    >
                      Forgot password?
                    </Link>
                  </div>
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
                      autoComplete="current-password"
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
                    <p id="password-error" className="text-sm text-destructive">
                      {errors.password}
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
                      Logging in...
                    </>
                  ) : (
                    "Log in"
                  )}
                </Button>

                <p className="text-center text-sm text-muted-foreground">
                  Don't have an account?{" "}
                  <Link
                    to="/register"
                    className="text-primary hover:text-accent transition-colors font-medium"
                  >
                    Register now
                  </Link>
                </p>
              </form>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
