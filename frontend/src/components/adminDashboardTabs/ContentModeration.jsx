import React from 'react'
import { useEffect, useState } from "react";
import { useSelector } from "react-redux";
import axios from "axios";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";

const ContentModeration = () => {
    const { user } = useSelector((state) => state.auth);
    const [contents, setContents] = useState([]);
    const [loading, setLoading] = useState(true);
    //  call to backend to fetch user's tickets using user.id

    useEffect(() => {

        // when integrated with backend, uncomment below

        // if (!user?.id) return;
        // axios
        //     .get(`/api/events/user/${user.id}`)
        //     .then((res) => {
        //         setEvents(res.data);
        //     })
        //     .catch((err) => {
        //         console.error("Error fetching events:", err);
        //     })
        //     .finally(() => {
        //         setLoading(false);
        //     });

        // Mock data for content snippet(eg: event desc contains spam, hateful comment), posted by, reported by, location(chat or event    )
        const mockContents = [
            {
                id: 1,
                snippet: "This is a spammy content",
                postedBy: "User 1",
                reportedBy: "User 2",
                location: "Event 1",
            },
            {
                id: 2,
                snippet: "This is a hateful comment",
                postedBy: "User 2",
                reportedBy: "User 3",
                location: "Event 2",
            },
            {
                id: 3,
                snippet: "This is a spammy content",
                postedBy: "User 3",
                reportedBy: "User 4",
                location: "Event 3",
            },
            {
                id: 4,
                snippet: "This is a hateful comment",
                postedBy: "User 4",
                reportedBy: "User 5",
                location: "Event 4",
            },
            {
                id: 5,
                snippet: "This is a spammy content",
                postedBy: "User 5",
                reportedBy: "User 6",
                location: "Event 5",
            },
            {
                id: 6,
                snippet: "This is a hateful comment",
                postedBy: "User 6",
                reportedBy: "User 7",
                location: "Event 6",
            },
            {
                id: 7,
                snippet: "This is a spammy content",
                postedBy: "User 7",
                reportedBy: "User 8",
                location: "Event 7",
            },
            {
                id: 8,
                snippet: "This is a hateful comment",
                postedBy: "User 8",
                reportedBy: "User 9",
                location: "Event 8",
            },
            {
                id: 9,
                snippet: "This is a spammy content",
                postedBy: "User 9",
                reportedBy: "User 10",
                location: "Event 9",
            },
            {
                id: 10,
                snippet: "This is a hateful comment",
                postedBy: "User 10",
                reportedBy: "User 11",
                location: "Event 10",
            },



        ];
        setTimeout(() => {
            setContents(mockContents);
            setLoading(false);
        }, 1000); // simulate network delay

    }, [user]);






    return (
        <div>



            {loading ? (
                <div>Loading contents...</div>
            ) : contents.length === 0 ? (
                <div>No contents found.</div>
            ) : (
                // shadcn table with contents    |   posted by   |   reported by   |   location   |   action with switch button
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[100px]">Content ID</TableHead>
                            <TableHead>Content Snippet</TableHead>
                            <TableHead>Posted By</TableHead>
                            <TableHead>Reported By</TableHead>
                            <TableHead>Location</TableHead>
                            <TableHead>Actions</TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {contents.map((content) => (
                            <TableRow key={content.id}>
                                <TableCell className="font-medium">{content.id}</TableCell>
                                <TableCell>{content.snippet}</TableCell>
                                <TableCell>{content.postedBy}</TableCell>
                                <TableCell>{content.reportedBy}</TableCell>
                                <TableCell>{content.location}</TableCell>
                                <TableCell>
                                    <Button
                                        variant="outline"
                                        className="mr-2 cursor-pointer hover:bg-red-400"
                                        onClick={() => {
                                            // call to backend to delete content
                                        }}
                                    >
                                        Delete
                                    </Button>
                                    <Button
                                        variant="outline"
                                        className="cursor-pointer hover:bg-green-400"
                                        onClick={() => {
                                            // call to backend to delete content
                                        }}
                                    >
                                        Approve
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            )}

        </div >
    )
}

export default ContentModeration