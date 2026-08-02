export const mockDashboardStats = [
    {
        id: "stat-1",
        title: "Active Campaigns",
        value: 18,
        icon: "campaign",
        change: "+3 this month",
        percentage: 15,
        positive: true
    },
    {
        id: "stat-2",
        title: "Total Candidates",
        value: 265,
        icon: "users",
        change: "+18 this week",
        percentage: 7,
        positive: true
    },
    {
        id: "stat-3",
        title: "Interviews Scheduled",
        value: 91,
        icon: "robot",
        change: "+12 today",
        percentage: 12,
        positive: true
    },
    {
        id: "stat-4",
        title: "Hiring Success Rate",
        value: "92%",
        icon: "chart",
        change: "+5% vs last Q",
        percentage: 5,
        positive: true
    }
];

export const mockQuickActions = [
    {
        id: "qa-1",
        title: "Create Campaign",
        description: "Publish a new hiring role",
        icon: "plus",
        path: "/company/campaigns/new",
        color: "linear-gradient(135deg, #3B82F6, #60A5FA)"
    },
    {
        id: "qa-2",
        title: "Schedule Interview",
        description: "Arrange live or AI meetings",
        icon: "calendar",
        path: "/company/interviews",
        color: "linear-gradient(135deg, #10B981, #34D399)"
    },
    {
        id: "qa-3",
        title: "Generate Report",
        description: "Export recruitment numbers",
        icon: "download",
        path: "/company/exports",
        color: "linear-gradient(135deg, #F59E0B, #FBBF24)"
    }
];

export const mockHiringProgress = [
    { department: "Engineering", currentHires: 12, targetHires: 15, progress: 80 },
    { department: "AI & Data Science", currentHires: 4, targetHires: 6, progress: 66 },
    { department: "Product & Design", currentHires: 3, targetHires: 4, progress: 75 },
    { department: "Sales & Marketing", currentHires: 6, targetHires: 8, progress: 75 },
    { department: "Human Resources", currentHires: 1, targetHires: 1, progress: 100 }
];

export const mockTodayTasks = [
    { id: "task-1", task: "Review AI Match reports for Alexander Wright", done: false, priority: "High" },
    { id: "task-2", task: "Reschedule technical interview for Priya Sharma", done: true, priority: "Medium" },
    { id: "task-3", task: "Send feedback reports to 12 rejected candidates", done: false, priority: "Low" },
    { id: "task-4", task: "Approve budget draft for 'Principal LLM Architect'", done: false, priority: "High" },
    { id: "task-5", task: "Review candidate profiles compilation report", done: false, priority: "Medium" }
];

export const mockAnnouncements = [
    {
        id: "ann-1",
        title: "IntelliGPT Screening V4.5 Active",
        content: "We upgraded our base parser algorithms. Candidate match precision improved by 8% across all active campaigns.",
        date: "Today"
    },
    {
        id: "ann-2",
        title: "Referral Bonus Increase",
        content: "Internal referrals for all AI and Engineering senior openings will yield a $5,000 onboarding bonus starting this month.",
        date: "2 days ago"
    },
    {
        id: "ann-3",
        title: "Summer Candidate Engagement Rules",
        content: "Candidates not moving to screening within 7 days will automatically receive a friendly follow-up email from our AI agents.",
        date: "1 week ago"
    }
];
export default mockDashboardStats;
