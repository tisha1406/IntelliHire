export const dashboardStats = [

    {
        id: 1,
        title: "Active Campaigns",
        value: 18,
        icon: "campaign",
        change: "+3 this month",
    },

    {
        id: 2,
        title: "Candidates",
        value: 265,
        icon: "users",
        change: "+18 this week",
    },

    {
        id: 3,
        title: "AI Interviews",
        value: 91,
        icon: "robot",
        change: "+12 today",
    },

    {
        id: 4,
        title: "Completion Rate",
        value: "92%",
        icon: "chart",
        change: "+5%",
    },

];

export const quickActions = [

    {
        id: 1,
        title: "New Campaign",
        description: "Create a new hiring campaign",
        color: "#2563EB",
        icon: "plus",
    },

    {
        id: 2,
        title: "Invite Candidate",
        description: "Invite applicants by email",
        color: "#10B981",
        icon: "userPlus",
    },

    {
        id: 3,
        title: "Export Reports",
        description: "Download hiring reports",
        color: "#F59E0B",
        icon: "download",
    },

];

export const applicationTrend = {

    labels: [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
    ],

    values: [
        45,
        72,
        61,
        98,
        121,
        140,
    ],

};

export const candidateStatus = [

    {
        label: "Selected",
        value: 35,
        color: "#10B981",
    },

    {
        label: "Interview",
        value: 45,
        color: "#3B82F6",
    },

    {
        label: "Rejected",
        value: 20,
        color: "#EF4444",
    },

];

export const recentCampaigns = [

    {
        id: 1,
        title: "Software Engineer",
        department: "Engineering",
        applicants: 42,
        deadline: "30 Jul 2026",
        status: "Active",
    },

    {
        id: 2,
        title: "Frontend Developer",
        department: "Engineering",
        applicants: 28,
        deadline: "02 Aug 2026",
        status: "Active",
    },

    {
        id: 3,
        title: "AI Research Intern",
        department: "AI",
        applicants: 74,
        deadline: "12 Aug 2026",
        status: "Closed",
    },

    {
        id: 4,
        title: "HR Executive",
        department: "Human Resources",
        applicants: 14,
        deadline: "15 Aug 2026",
        status: "Draft",
    },

];

export const recentCandidates = [

    {
        id: 1,
        name: "John Smith",
        position: "Software Engineer",
        score: 92,
        status: "Interview Scheduled",
    },

    {
        id: 2,
        name: "Sarah Johnson",
        position: "Frontend Developer",
        score: 88,
        status: "Under Review",
    },

    {
        id: 3,
        name: "David Brown",
        position: "AI Research Intern",
        score: 95,
        status: "Selected",
    },

    {
        id: 4,
        name: "Emily Davis",
        position: "HR Executive",
        score: 81,
        status: "Assessment Pending",
    },

];

export const activityTimeline = [

    {

        id:1,

        type:"campaign",

        title:"New Campaign Created",

        description:"Frontend Developer campaign has been published.",

        time:"10 mins ago"

    },

    {

        id:2,

        type:"candidate",

        title:"Candidate Shortlisted",

        description:"John Smith moved to Interview Round.",

        time:"35 mins ago"

    },

    {

        id:3,

        type:"interview",

        title:"AI Interview Completed",

        description:"Sarah Johnson scored 92%.",

        time:"1 hour ago"

    },

    {

        id:4,

        type:"report",

        title:"Hiring Report Generated",

        description:"Monthly hiring report exported.",

        time:"3 hours ago"

    }

];

export const upcomingInterviews = [

    {
        id:1,
        candidate:"Sarah Johnson",
        role:"Software Engineer",
        time:"09:30 AM",
        type:"AI Interview",
    },

    {
        id:2,
        candidate:"David Brown",
        role:"Frontend Developer",
        time:"11:00 AM",
        type:"Technical Round",
    },

    {
        id:3,
        candidate:"Emily Davis",
        role:"HR Executive",
        time:"02:30 PM",
        type:"HR Discussion",
    },

    {
        id:4,
        candidate:"John Smith",
        role:"AI Research Intern",
        time:"04:00 PM",
        type:"Final Round",
    },

];
