// Create 50 realistic notification records
export const mockNotifications = [
    {
        id: "notif-001",
        type: "recruitment",
        title: "New Application Received",
        message: "Alexander Wright submitted an application for Lead Frontend Engineer (React).",
        time: "5 minutes ago",
        unread: true,
        created: "2026-07-22T13:44:00Z"
    },
    {
        id: "notif-002",
        type: "candidate",
        title: "AI Screening Completed",
        message: "Priya Sharma scored 90/100 in the AI Technical Assessment for Senior AI Scientist.",
        time: "12 minutes ago",
        unread: true,
        created: "2026-07-22T13:37:00Z"
    },
    {
        id: "notif-003",
        type: "security",
        title: "New Device Login",
        message: "A login was detected from Chrome on macOS from London, UK for Dev Patel.",
        time: "45 minutes ago",
        unread: true,
        created: "2026-07-22T13:04:00Z"
    },
    {
        id: "notif-004",
        type: "system",
        title: "Subscription Renewed",
        message: "IntelliHire Enterprise Plan successfully renewed for August 2026.",
        time: "2 hours ago",
        unread: false,
        created: "2026-07-22T11:49:00Z"
    },
    {
        id: "notif-005",
        type: "candidate",
        title: "Interview Rescheduled",
        message: "Sarah Chen rescheduled her AI Interview to tomorrow at 10:00 AM.",
        time: "3 hours ago",
        unread: true,
        created: "2026-07-22T10:49:00Z"
    },
    {
        id: "notif-006",
        type: "recruitment",
        title: "Campaign Reached Deadline",
        message: "The Product Designer (UX/UI) campaign deadline has passed. 64 candidates total.",
        time: "4 hours ago",
        unread: false,
        created: "2026-07-22T09:49:00Z"
    },
    {
        id: "notif-007",
        type: "system",
        title: "Data Backup Complete",
        message: "Global encrypted candidate profiles database successfully backed up to AWS Glacier.",
        time: "6 hours ago",
        unread: false,
        created: "2026-07-22T07:49:00Z"
    },
    {
        id: "notif-008",
        type: "recruitment",
        title: "New Application Received",
        message: "Elena Rostova added candidate Aisha Diallo to Growth Marketing campaign.",
        time: "7 hours ago",
        unread: false,
        created: "2026-07-22T06:49:00Z"
    },
    {
        id: "notif-009",
        type: "security",
        title: "Password Changed",
        message: "The password for admin user Sarah Jenkins was updated successfully.",
        time: "9 hours ago",
        unread: false,
        created: "2026-07-22T04:49:00Z"
    },
    {
        id: "notif-010",
        type: "candidate",
        title: "AI Interview Finished",
        message: "Marcus Dupont finished the AI Portfolio Review. Match rating: 92%.",
        time: "10 hours ago",
        unread: true,
        created: "2026-07-22T03:49:00Z"
    },
    {
        id: "notif-011",
        type: "recruitment",
        title: "New Campaign Launched",
        message: "DevOps & Infrastructure Lead campaign was successfully published by Sarah Jenkins.",
        time: "1 day ago",
        unread: false,
        created: "2026-07-21T12:00:00Z"
    },
    {
        id: "notif-012",
        type: "candidate",
        title: "Assessment Failed",
        message: "Nathan Drake failed the screening threshold for Office Operations (Score: 60%).",
        time: "1 day ago",
        unread: false,
        created: "2026-07-21T10:00:00Z"
    },
    {
        id: "notif-013",
        type: "system",
        title: "Model Upgrade Complete",
        message: "AI Screening algorithms upgraded to IntelliGPT-4.5. Match precision improved.",
        time: "1 day ago",
        unread: false,
        created: "2026-07-21T08:00:00Z"
    },
    {
        id: "notif-014",
        type: "security",
        title: "API Key Generated",
        message: "A new integration API key was created by user Dev Patel.",
        time: "2 days ago",
        unread: false,
        created: "2026-07-20T15:30:00Z"
    },
    {
        id: "notif-015",
        type: "recruitment",
        title: "Offer Accepted",
        message: "Lukas Müller has accepted the employment offer for Technical Support Engineer.",
        time: "2 days ago",
        unread: true,
        created: "2026-07-20T11:00:00Z"
    },
    // Adding 35 more items to make total 50
    ...Array.from({ length: 35 }).map((_, i) => {
        const idNum = i + 16;
        const types = ["recruitment", "candidate", "system", "security"];
        const type = types[i % 4];
        const titles = {
            recruitment: "Applicant Pipeline Update",
            candidate: "AI Assessment Scheduled",
            system: "API Limit Warning",
            security: "Access Granted Token"
        };
        const messages = {
            recruitment: `Hiring Manager reviewed candidate #${100 + idNum} for role matching.`,
            candidate: `Candidate #${200 + idNum} scheduled AI interview screening loop.`,
            system: `Monthly webhook integration API capacity is at ${60 + (i * 2)}%.`,
            security: `OAuth session token issued for team member ID #${300 + idNum}.`
        };
        const hours = i + 3;
        return {
            id: `notif-0${idNum}`,
            type,
            title: titles[type],
            message: messages[type],
            time: hours > 24 ? `${Math.floor(hours/24)} days ago` : `${hours} hours ago`,
            unread: idNum % 5 === 0,
            created: new Date(Date.now() - hours * 60 * 60 * 1000).toISOString()
        };
    })
];
