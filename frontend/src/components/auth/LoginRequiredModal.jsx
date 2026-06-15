import React from "react";
import { X } from "lucide-react";
import { useNavigate } from "react-router";

const LoginRequiredModal = ({ isOpen, onClose }) => {
    const navigate = useNavigate();

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-white rounded-xl shadow-lg w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
                {/* Content */}
                <div className="p-8 flex flex-col items-center text-center">
                    <h2 className="text-2xl font-bold text-gray-900 mb-2">
                        You are not logged in!
                    </h2>
                    <p className="text-gray-500 mb-8">
                        Please Login first to proceed further
                    </p>

                    <div className="flex flex-col sm:flex-row gap-4 w-full">
                        <button
                            onClick={() => navigate("/login")}
                            className="bg-black text-white py-2.5 rounded-lg font-semibold hover:opacity-90 transition w-full sm:flex-1"
                        >
                            Login
                        </button>
                        <button
                            onClick={onClose}
                            className="bg-white border border-gray-300 text-gray-700 py-2.5 rounded-lg font-semibold hover:bg-gray-50 transition w-full sm:flex-1"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LoginRequiredModal;
