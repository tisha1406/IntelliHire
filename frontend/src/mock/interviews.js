export const mockInterviewStats = {
    upcoming: 14,
    completed: 122,
    cancelled: 8,
    averageScore: 84
};

export const mockInterviews = [
    {
        id: "int-001",
        candidate: "Alexander Wright",
        position: "Lead Frontend Engineer (React)",
        interviewer: "AI Agent & Alex Mercer",
        date: "2026-07-22",
        time: "14:30",
        status: "Completed",
        aiScore: 96,
        evaluation: {
            summary: "Alexander demonstrated absolute mastery of advanced frontend concepts, web performance optimization, and clean state designs.",
            strengths: ["Exceptional React architectural logic", "Highly detailed performance rendering knowledge", "Clear explainability of systems design"],
            weaknesses: ["Prefers CSS Modules; less warm towards utility-first frameworks", "Might be slightly over-qualified for junior code mentoring"],
            recommendation: "Strong Hire",
            questions: [
                {
                    q: "How would you optimize a large list of 10,000 React items updates dynamically?",
                    a: "I would use a virtualization library like react-window, memoize list rows with React.memo, leverage CSS content-visibility: auto, and throttle scroll listener updates.",
                    sentiment: "Excellent",
                    score: 98
                },
                {
                    q: "Explain how React 19 handles Server Components compared to standard client rendering.",
                    a: "Server Components execute directly on the server to reduce client bundle sizes and compile state. They stream standard HTML tags and interactive nodes to the client.",
                    sentiment: "Very Good",
                    score: 94
                }
            ]
        }
    },
    {
        id: "int-002",
        candidate: "Priya Sharma",
        position: "Senior AI Research Scientist",
        interviewer: "AI Agent & Dev Patel",
        date: "2026-07-23",
        time: "10:00",
        status: "Scheduled",
        aiScore: null,
        evaluation: null
    },
    {
        id: "int-003",
        candidate: "Marcus Dupont",
        position: "Product Designer (UX/UI)",
        interviewer: "AI Agent & Diana Prince",
        date: "2026-07-20",
        time: "16:00",
        status: "Completed",
        aiScore: 89,
        evaluation: {
            summary: "Marcus possesses an elegant minimalist visual style. Explained layout spaces and micro-interaction mechanics in high detail.",
            strengths: ["Clean Figma organization systems", "Strong UX user testing workflow", "Responsive layout principles"],
            weaknesses: ["Lacks knowledge of technical React rendering constraints", "Lacks SQL dashboard metrics tracking experience"],
            recommendation: "Hire",
            questions: [
                {
                    q: "What is your approach to designing a complex B2B settings interface?",
                    a: "I group configurations into distinct tabs, use sliders for granular settings, clear labels, inline toggle actions, and prevent layout shifts during selections.",
                    sentiment: "Very Good",
                    score: 90
                }
            ]
        }
    },
    {
        id: "int-004",
        candidate: "Sarah Chen",
        position: "Senior Backend Developer (Go)",
        interviewer: "AI Agent & Alex Mercer",
        date: "2026-07-18",
        time: "11:30",
        status: "Completed",
        aiScore: 95,
        evaluation: {
            summary: "Sarah answered backend systems scaling, query indexing, and container load balancing tests with perfect conceptual precision.",
            strengths: ["Flawless Golang concurrent patterns", "Deep postgres deadlock debugging experience", "Excellent container design patterns"],
            weaknesses: ["Mainly focused on systems; very low CSS/JS interest"],
            recommendation: "Strong Hire",
            questions: [
                {
                    q: "Explain database locking and how you prevent deadlocks in Go concurrency.",
                    a: "I enforce locks in a consistent order, use connection timeouts, monitor long transactions, and use Go's sync.Mutex or channels to regulate shared memory safely.",
                    sentiment: "Excellent",
                    score: 96
                }
            ]
        }
    },
    {
        id: "int-005",
        candidate: "Carlos Mendez",
        position: "Frontend Developer",
        interviewer: "AI Agent & Anna Kovac",
        date: "2026-07-24",
        time: "15:00",
        status: "Scheduled",
        aiScore: null,
        evaluation: null
    },
    {
        id: "int-006",
        candidate: "Emily Watson",
        position: "Technical Product Manager",
        interviewer: "AI Agent & Diana Prince",
        date: "2026-07-19",
        time: "11:00",
        status: "Completed",
        aiScore: 86,
        evaluation: {
            summary: "Emily demonstrated a good balance of technical knowledge and agile management frameworks. Clear communicator.",
            strengths: ["Excellent requirements gathering", "Clear developer communication", "Strong API documentation skills"],
            weaknesses: ["Familiar with basic SQL query designs but not database optimization"],
            recommendation: "Hire",
            questions: [
                {
                    q: "How do you resolve conflicts between engineering and marketing team requests?",
                    a: "I prioritize based on company OKRs, customer value impact, implementation cost, and run quick scoping studies to find balanced solutions.",
                    sentiment: "Good",
                    score: 86
                }
            ]
        }
    },
    {
        id: "int-007",
        candidate: "Yuki Tanaka",
        position: "DevOps & Infrastructure Lead",
        interviewer: "AI Agent & Alex Mercer",
        date: "2026-07-25",
        time: "09:00",
        status: "Scheduled",
        aiScore: null,
        evaluation: null
    },
    {
        id: "int-008",
        candidate: "Sophia Martinez",
        position: "Growth Marketing Manager",
        interviewer: "AI Agent & Marcus Vance",
        date: "2026-07-22",
        time: "11:00",
        status: "Completed",
        aiScore: 80,
        evaluation: {
            summary: "Sophia is very creative in paid acquisition channels. However, her data modeling capabilities are slightly basic.",
            strengths: ["Excellent copywriting strategy", "Highly familiar with Google Ads algorithms", "Creative branding initiatives"],
            weaknesses: ["Needs training on SQL and complex cohort analytics tools"],
            recommendation: "Hold / Hire",
            questions: [
                {
                    q: "How do you calculate LTV:CAC and optimize paid channel spend?",
                    a: "LTV is Average Order Value times Purchase Frequency times Customer Lifespan. CAC is Total Sales & Marketing costs divided by Customers Acquired. I optimize by shifting budget to higher LTV campaigns.",
                    sentiment: "Good",
                    score: 82
                }
            ]
        }
    },
    {
        id: "int-009",
        candidate: "Lukas Müller",
        position: "Technical Support Engineer",
        interviewer: "AI Agent & Dev Patel",
        date: "2026-07-15",
        time: "14:00",
        status: "Completed",
        aiScore: 93,
        evaluation: {
            summary: "Lukas represents a stellar support profile. Calm, thorough, technical, and empathetic. Solved our mock debugging tasks with high scores.",
            strengths: ["Deep developer empathy", "Methodical API debugging", "Strong written explanations"],
            weaknesses: ["No experience with container deployments"],
            recommendation: "Strong Hire",
            questions: [
                {
                    q: "How do you handle a customer who claims our webhook isn't triggering?",
                    a: "I verify our delivery logs, check customer integration URLs, inspect error response codes, suggest tools like Webhook.site to isolate, and verify retry policies.",
                    sentiment: "Excellent",
                    score: 95
                }
            ]
        }
    },
    {
        id: "int-010",
        candidate: "David Kim",
        position: "Enterprise Account Executive",
        interviewer: "AI Agent & Marcus Vance",
        date: "2026-07-27",
        time: "16:30",
        status: "Scheduled",
        aiScore: null,
        evaluation: null
    }
];
export default mockInterviews;
