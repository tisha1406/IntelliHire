// Hiring Trend (Monthly Candidate Counts)
export const mockHiringTrend = [
    { month: "Jan", applications: 45, selections: 5 },
    { month: "Feb", applications: 72, selections: 8 },
    { month: "Mar", applications: 61, selections: 6 },
    { month: "Apr", applications: 98, selections: 10 },
    { month: "May", applications: 121, selections: 14 },
    { month: "Jun", applications: 140, selections: 15 },
    { month: "Jul", applications: 185, selections: 21 },
    { month: "Aug", applications: 160, selections: 18 },
    { month: "Sep", applications: 130, selections: 14 },
    { month: "Oct", applications: 115, selections: 12 },
    { month: "Nov", applications: 95, selections: 9 },
    { month: "Dec", applications: 88, selections: 8 }
];

// Source of Candidates (Channels)
export const mockCandidateSources = [
    { source: "LinkedIn", value: 340, percentage: 40, color: "#0A66C2" },
    { source: "Referrals", value: 170, percentage: 20, color: "#10B981" },
    { source: "Direct Search", value: 128, percentage: 15, color: "#8B5CF6" },
    { source: "Job Boards", value: 127, percentage: 15, color: "#3B82F6" },
    { source: "Agencies", value: 85, percentage: 10, color: "#F59E0B" }
];

// Hiring Funnel Stages
export const mockHiringFunnel = [
    { stage: "Applied", count: 850, percentage: 100, label: "850 Applications" },
    { stage: "AI Screened", count: 510, percentage: 60, label: "510 Cleared Screen" },
    { stage: "Assessments", count: 306, percentage: 36, label: "306 Scheduled" },
    { stage: "Interviews", count: 122, percentage: 14, label: "122 Technical/HR" },
    { stage: "Offered", count: 48, percentage: 5.6, label: "48 Job Offers" },
    { stage: "Hired", count: 38, percentage: 4.4, label: "38 Accepted" }
];

// Department Distribution
export const mockDepartmentHiring = [
    { department: "Engineering", openJobs: 6, applicants: 410, hires: 18, budget: "$450k" },
    { department: "AI & Data Science", openJobs: 3, applicants: 198, hires: 8, budget: "$320k" },
    { department: "Product & Design", openJobs: 2, applicants: 117, hires: 5, budget: "$150k" },
    { department: "Sales & Marketing", openJobs: 3, applicants: 284, hires: 6, budget: "$200k" },
    { department: "Human Resources", openJobs: 1, applicants: 29, hires: 1, budget: "$65k" }
];

// Monthly Comparison (2025 vs 2026 Applications Volume)
export const mockMonthlyComparison = [
    { month: "Jan", year2025: 35, year2026: 45 },
    { month: "Feb", year2025: 48, year2026: 72 },
    { month: "Mar", year2025: 55, year2026: 61 },
    { month: "Apr", year2025: 70, year2026: 98 },
    { month: "May", year2025: 85, year2026: 121 },
    { month: "Jun", year2025: 92, year2026: 140 },
    { month: "Jul", year2025: 110, year2026: 185 }
];

// Recruiter Performance Scorecard
export const mockRecruiterPerformance = [
    { name: "Sarah Jenkins", activeCampaigns: 5, averageTimeToHire: "19 days", selections: 14, offerAcceptanceRate: 92 },
    { name: "Dev Patel", activeCampaigns: 4, averageTimeToHire: "22 days", selections: 8, offerAcceptanceRate: 88 },
    { name: "Anna Kovac", activeCampaigns: 3, averageTimeToHire: "24 days", selections: 5, offerAcceptanceRate: 83 },
    { name: "Marcus Vance", activeCampaigns: 3, averageTimeToHire: "28 days", selections: 6, offerAcceptanceRate: 90 },
    { name: "Elena Rostova", activeCampaigns: 3, averageTimeToHire: "21 days", selections: 5, offerAcceptanceRate: 85 }
];

// Global KPIs
export const mockKPIs = {
    averageTimeToHire: { value: "22 days", change: "-3 days", percentage: 12, positive: true },
    offerAcceptanceRate: { value: "87.6%", change: "+2.4%", percentage: 2.8, positive: true },
    totalApplications: { value: "1,038", change: "+15%", percentage: 15, positive: true },
    totalInterviews: { value: "382", change: "+8%", percentage: 8, positive: true },
    selections: { value: "42", change: "+5 this month", percentage: 13, positive: true }
};
export default mockKPIs;
