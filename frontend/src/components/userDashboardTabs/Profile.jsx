import React from "react";
import { useSelector } from "react-redux";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useRef, useState, useEffect } from "react";
import userApiService from "@/services/userApiService";
import { toast } from "sonner";
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar";

import { Camera } from "lucide-react";
import TwoFactorSetup from "@/components/TwoFactorSetup";
import { Switch } from "@/components/ui/switch";
import authApiService from "@/services/authApiService";
import { TagInput } from "@/components/TagInput";


const Profile = () => {
    const user = useSelector((state) => state.auth.user);
    const fileInputRef = useRef(null);
    const [profileData, setProfileData] = useState({
        first_names: "",
        last_name: "",
        email: "",
        phone_number: "",
        street_address: "",
        city: "",
        zip_code: "",
        country: "",
        interests: [],
    });
    const [passwords, setPasswords] = useState({
        currentPassword: "",
        newPassword: "",
        confirmNewPassword: "",
    });
    const [loading, setLoading] = useState(true);
    
    // 2FA settings
    const [is2FAEnabled, setIs2FAEnabled] = useState(false);
    const [is2FASetupOpen, setIs2FASetupOpen] = useState(false);

    useEffect(() => {
        const fetchProfile = async () => {
            if (user?.user?.id) {
                try {
                    const data = await userApiService.fetchUserDetails(user.user.id);
                    console.log(data);
                    setProfileData({
                        first_names: data.first_names || "",
                        last_name: data.last_name || "",
                        email: data.email || "",
                        phone_number: data.phone_number || "",
                        street_address: data.street_address || "",
                        city: data.city || "",
                        zip_code: data.zip_code || "",
                        country: data.country || "",
                        interests: data.interests || [],
                    });
                    // Sync 2FA status
                    setIs2FAEnabled(!!data.is_two_factor_enabled);
                } catch (error) {
                    console.error("Error fetching profile:", error);
                } finally {
                    setLoading(false);
                }
            }
        };
        fetchProfile();
    }, [user]);

    const handleInputChange = (e) => {
        const { id, value } = e.target;
        setProfileData((prev) => ({
            ...prev,
            [id]: value,
        }));
    };

    const handlePasswordChange = (e) => {
        const { id, value } = e.target;
        setPasswords((prev) => ({
            ...prev,
            [id]: value,
        }));
    };

    const handleSave = async () => {
        if (!user?.user?.id) return;

        const payload = {
            first_names: profileData.first_names,
            last_name: profileData.last_name,
            phone_number: profileData.phone_number,
            street_address: profileData.street_address,
            city: profileData.city,
            zip_code: profileData.zip_code,
            country: profileData.country,
            email: profileData.email,
            interests: profileData.interests,
        };

        try {
            await userApiService.saveUserDetails(user.user.id, payload);
            toast.success("Profile updated successfully!");
        } catch (error) {
            console.error("Error saving profile:", error);
            toast.error("Failed to update profile.");
        }
    };

    const handleUpdatePassword = async () => {
        if (!user?.user?.id) return;

        if (passwords.newPassword !== passwords.confirmNewPassword) {
            toast.error("New passwords do not match!");
            return;
        }

        if (passwords.newPassword.length < 6) {
            toast.error("Password must be at least 6 characters long.");
            return;
        }

        try {
            await userApiService.changePassword(user.user.id, {
                old_password: passwords.currentPassword,
                new_password: passwords.newPassword,
                confirm_password: passwords.confirmNewPassword,
            });
            toast.success("Password updated successfully!");
            setPasswords({
                currentPassword: "",
                newPassword: "",
                confirmNewPassword: "",
            });
        } catch (error) {
            console.error("Error updating password:", error);
            toast.error(error.response?.data?.detail || "Failed to update password.");
        }
    };

    const handleClick = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
        }
    };

    const handle2FAToggle = async (checked) => {
        if (checked) {
            // Start setup flow
            setIs2FASetupOpen(true);
        } else {
            try {
                await authApiService.disable2FA();
                setIs2FAEnabled(false);
                toast.success("Two-Factor Authentication disabled.");
            } catch (error) {
                toast.error("Failed to disable 2FA.");
            }
        }
    };
    
    const handle2FASuccess = (enabled) => {
         setIs2FAEnabled(enabled);
    };

    const getInitials = () => {
        const first = profileData.first_names?.charAt(0) || "";
        const last = profileData.last_name?.charAt(0) || "";
        return (first + last).toUpperCase() || "U";
    };


    return (
        <div className="space-y-6">
            <Tabs defaultValue="personalInfo" className="w-full">
                <TabsList className="flex gap-8 bg-transparent p-0 mb-6">

                    <TabsTrigger
                        value="personalInfo"
                        className="
        relative pb-2 text-base font-medium
        data-[state=active]:text-primary
        data-[state=inactive]:text-muted-foreground
        after:content-['']
        after:absolute after:left-0 after:bottom-0
        after:w-full after:h-[2px]
        after:bg-primary
        after:scale-x-0
        data-[state=active]:after:scale-x-100
        after:transition-transform
        after:origin-left
      "
                    >
                        Personal Information

                    </TabsTrigger>


                    <TabsTrigger
                        value="security"
                        className="
        relative pb-2 text-base font-medium
        data-[state=active]:text-primary
        data-[state=inactive]:text-muted-foreground
        after:content-['']
        after:absolute after:left-0 after:bottom-0
        after:w-full after:h-[2px]
        after:bg-primary
        after:scale-x-0
        data-[state=active]:after:scale-x-100
        after:transition-transform
        after:origin-left
      "
                    >
                        Password and Security
                    </TabsTrigger>

                </TabsList>

                <TabsContent value="personalInfo" className="mt-4">
                    <Card className="bg-white/60 dark:bg-card/60 backdrop-blur-sm border-primary/10 shadow-sm">
                        <CardContent className="p-6">
                            <div className="flex flex-col items-left gap-3">

                                <div className="flex items-center gap-6 mb-8">

                                    <div
                                        className="relative cursor-pointer group"
                                        onClick={handleClick}
                                    >
                                        <Avatar className="w-28 h-28 rounded-full border-2 border-primary/20 shadow-md">
                                            <AvatarImage src={user.image ? URL.createObjectURL(image) : undefined} />
                                            <AvatarFallback className="text-3xl font-bold bg-primary/10 text-primary">
                                                {getInitials()}
                                            </AvatarFallback>
                                        </Avatar>

                                        <div className="
          absolute inset-0 rounded-full bg-black/40
          flex items-center justify-center opacity-0
          group-hover:opacity-100 transition duration-300
          ">
                                            <Camera className="text-white w-8 h-8" />
                                        </div>
                                    </div>

                                    <input
                                        type="file"
                                        accept="image/*"
                                        ref={fileInputRef}
                                        className="hidden"
                                        onChange={handleFileChange}
                                    />

                                    <div>
                                        <h2 className="text-2xl font-bold text-foreground">
                                            {profileData.first_names} {profileData.last_name}
                                        </h2>
                                        <p className="text-muted-foreground">{profileData.email}</p>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">





                                <div>
                                    <Label htmlFor="first_names" className="text-muted-foreground mb-1.5 block">First Name</Label>
                                    <Input
                                        type="text"
                                        id="first_names"
                                        value={profileData.first_names}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="last_name" className="text-muted-foreground mb-1.5 block">Last Name</Label>
                                    <Input
                                        type="text"
                                        id="last_name"
                                        value={profileData.last_name}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="email" className="text-muted-foreground mb-1.5 block">Email</Label>
                                    <Input
                                        type="email"
                                        id="email"
                                        value={profileData.email}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                        disabled
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="phone_number" className="text-muted-foreground mb-1.5 block">Phone Number</Label>
                                    <Input
                                        type="text"
                                        id="phone_number"
                                        value={profileData.phone_number}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="street_address" className="text-muted-foreground mb-1.5 block">Street Address</Label>
                                    <Input
                                        type="text"
                                        id="street_address"
                                        value={profileData.street_address}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="city" className="text-muted-foreground mb-1.5 block">City</Label>
                                    <Input
                                        type="text"
                                        id="city"
                                        value={profileData.city}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="zip_code" className="text-muted-foreground mb-1.5 block">Zip Code</Label>
                                    <Input
                                        type="text"
                                        id="zip_code"
                                        value={profileData.zip_code}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="country" className="text-muted-foreground mb-1.5 block">Country</Label>
                                    <Input
                                        type="text"
                                        id="country"
                                        value={profileData.country}
                                        onChange={handleInputChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div className="sm:col-span-2">
                                    <Label htmlFor="interests" className="text-muted-foreground mb-1.5 block">Interests / Preferences</Label>
                                    <TagInput
                                        value={profileData.interests}
                                        onChange={(tags) => setProfileData(prev => ({...prev, interests: tags}))}
                                        placeholder="Type an interest and press Enter"
                                    />
                                </div>
                            </div>
                            <div className="flex justify-end mt-8">
                                <Button
                                    type="submit"
                                    onClick={handleSave}
                                    className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 h-11 text-base shadow-lg shadow-primary/20 transition-all hover:scale-[1.02]"
                                >
                                    Save Changes
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>
                <TabsContent value="security" className="mt-4">
                    <Card className="bg-white/60 dark:bg-card/60 backdrop-blur-sm border-primary/10 shadow-sm">
                        <CardContent className="p-6">
                            <div className="grid grid-cols-1 w-full max-w-2xl gap-6">
                                <div>
                                    <Label htmlFor="currentPassword" className="text-muted-foreground mb-1.5 block">Current Password</Label>
                                    <Input
                                        type="password"
                                        id="currentPassword"
                                        value={passwords.currentPassword}
                                        onChange={handlePasswordChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="newPassword" className="text-muted-foreground mb-1.5 block">New Password</Label>
                                    <Input
                                        type="password"
                                        id="newPassword"
                                        value={passwords.newPassword}
                                        onChange={handlePasswordChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                                <div>
                                    <Label htmlFor="confirmNewPassword" className="text-muted-foreground mb-1.5 block">Confirm New Password</Label>
                                    <Input
                                        type="password"
                                        id="confirmNewPassword"
                                        value={passwords.confirmNewPassword}
                                        onChange={handlePasswordChange}
                                        className="bg-white/50 dark:bg-card/50 border-primary/10 focus:ring-primary/20 focus:border-primary/30 h-11"
                                    />
                                </div>
                            </div>
                            <div className="flex justify-start mt-8">
                                <Button
                                    type="submit"
                                    onClick={handleUpdatePassword}
                                    className="bg-primary hover:bg-primary/90 text-primary-foreground px-8 h-11 text-base shadow-lg shadow-primary/20 transition-all hover:scale-[1.02]"
                                >
                                    Update Password
                                </Button>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="bg-white/60 dark:bg-card/60 backdrop-blur-sm border-primary/10 shadow-sm mt-6">
                         <CardContent className="p-6">
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label className="text-base font-semibold">Two-Factor Authentication</Label>
                                    <p className="text-sm text-muted-foreground">
                                        Secure your account with Google Authenticator.
                                    </p>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className={`text-sm ${is2FAEnabled ? "text-green-600 font-medium" : "text-muted-foreground"}`}>
                                        {is2FAEnabled ? "Enabled" : "Disabled"}
                                    </span>
                                    <Switch
                                        checked={is2FAEnabled}
                                        onCheckedChange={handle2FAToggle}
                                    />
                                </div>
                            </div>
                         </CardContent>
                    </Card>
                </TabsContent>
            </Tabs>

            <TwoFactorSetup 
                isOpen={is2FASetupOpen} 
                onClose={() => setIs2FASetupOpen(false)}
                onStatusChange={handle2FASuccess}
            />
        </div>
    );
};

export default Profile;
