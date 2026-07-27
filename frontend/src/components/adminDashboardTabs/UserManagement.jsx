import React from 'react'
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Search, MessageSquare } from "lucide-react";

import socketService from "@/services/socketService";

import { baseUrl } from "@/routes";
import { Button } from "@/components/ui/button";

const UserManagement = () => {
    const { user } = useSelector((state) => state.auth);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(10);
    const [search, setSearch] = useState("");
    const [debouncedSearch, setDebouncedSearch] = useState("");
    const [totalPages, setTotalPages] = useState(1);

    // Debounce search input
    useEffect(() => {
        const timer = setTimeout(() => {
            setDebouncedSearch(search);
            setPage(1); // Reset to first page on new search
        }, 500);
        return () => clearTimeout(timer);
    }, [search]);

    useEffect(() => {
        if (!user?.access_token) return;

        setLoading(true);
        const config = {
            headers: {
                Authorization: `Bearer ${user.access_token}`,
            },
            params: {
                page: page,
                page_size: pageSize,
                search: debouncedSearch || null,
            },
        };

        axios
            .get(`${baseUrl}admins/users`, config)
            .then((res) => {
                const data = res.data?.data;
                const items = data?.items || [];
                setUsers(items);

                if (data?.pagination?.pages) {
                    setTotalPages(data.pagination.pages);
                } else {
                    setTotalPages(1);
                }
            })
            .catch((err) => {
                console.error("Error fetching users:", err);
            })
            .finally(() => {
                setLoading(false);
            });
    }, [user, page, pageSize, debouncedSearch]);

    return (
        <div className="space-y-6">
            {/* Search Bar */}
            <div className="flex justify-end">
                <div className="relative w-full md:w-72">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <input
                        type="text"
                        placeholder="Search users..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 bg-white/50 dark:bg-card/50 border border-primary/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/30 transition-all placeholder:text-muted-foreground/70"
                    />
                </div>
            </div>

            {loading ? (
                <div className="flex justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
            ) : users.length === 0 ? (
                <div className="text-center py-12 text-muted-foreground bg-white/30 dark:bg-card/30 rounded-xl border border-dashed border-primary/10">
                    No users found.
                </div>
            ) : (
                <>
                    <div className="rounded-xl border border-primary/10 overflow-hidden bg-white/60 dark:bg-card/60 backdrop-blur-sm shadow-sm">
                        <Table>
                            <TableHeader className="bg-primary/5">
                                <TableRow className="hover:bg-transparent border-primary/10">
                                    <TableHead className="w-[100px] font-bold text-primary">User ID</TableHead>
                                    <TableHead className="font-bold text-primary">Name</TableHead>
                                    <TableHead className="font-bold text-primary">Email</TableHead>
                                    <TableHead className="font-bold text-primary">Role</TableHead>
                                    <TableHead className="font-bold text-primary">Status</TableHead>
                                    <TableHead className="font-bold text-primary">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {users.map((u) => (
                                    <TableRow key={u.id} className="hover:bg-primary/5 transition-colors border-primary/5">
                                        <TableCell className="font-medium text-muted-foreground">#{u.id}</TableCell>
                                        <TableCell className="font-medium">{u.first_names} {u.last_name}</TableCell>
                                        <TableCell className="text-muted-foreground">{u.email}</TableCell>
                                        <TableCell>
                                            <Badge variant="outline" className="bg-primary/5 border-primary/20 text-primary">
                                                {Array.isArray(u.roles) ? u.roles.join(", ") : u.roles}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Badge
                                                variant="secondary"
                                                className={`${(u.status === "Active" || !u.status)
                                                    ? "bg-green-500/10 text-green-600 border-green-500/20"
                                                    : "bg-red-500/10 text-red-600 border-red-500/20"
                                                    }`}
                                            >
                                                {u.status || "Active"}
                                            </Badge>
                                        </TableCell>
                                        <TableCell>
                                            <Switch
                                                disabled={true}
                                                checked={u.status === "Active" || !u.status} // Assuming default active if not specified
                                                onCheckedChange={(checked) => {
                                                    if (checked) {
                                                        // call to backend to activate user
                                                    } else {
                                                        // call to backend to deactivate user
                                                    }
                                                }}
                                                className="data-[state=checked]:bg-green-500"
                                            />
                                            {/* if the user is admin dont show  */}
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                onClick={() => socketService.joinDirect(u.id)}
                                                className={u.roles.includes("admin") ? "hidden" : "h-8 w-8 ml-2 text-muted-foreground hover:text-primary"}
                                                title="Message User"
                                            >
                                                <MessageSquare className="h-4 w-4" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    </div>

                    {/* Pagination Controls */}
                    {totalPages > 1 && (
                        <div className="flex justify-center items-center gap-2 mt-6">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage((p) => Math.max(1, p - 1))}
                                disabled={page === 1 || loading}
                                className="border-primary/20 hover:bg-primary/5"
                            >
                                Previous
                            </Button>
                            <div className="flex items-center gap-1 px-2">
                                <span className="text-sm font-medium text-muted-foreground">Page</span>
                                <span className="text-sm font-bold text-primary">{page}</span>
                                <span className="text-sm font-medium text-muted-foreground">of {totalPages}</span>
                            </div>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => setPage((p) => p + 1)}
                                disabled={page >= totalPages || loading}
                                className="border-primary/20 hover:bg-primary/5"
                            >
                                Next
                            </Button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default UserManagement