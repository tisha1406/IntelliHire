// ============================================================
// INTELLIHIRE — CANDIDATE PORTAL PLACEHOLDER DATA (B2B CAMPAIGN)
// All pages consume this file. Replace with API calls later.
// ============================================================

export const candidateProfile = {
  id: "cand_b2b_001",
  name: "Priya Sharma",
  email: "priya.sharma@example.com",
  phone: "+91 98765 43210",
  avatar: null,
  role: "candidate",
  memberSince: "2025-07-01",
  lastLogin: "Just now",
};

export const campaignConfig = {
  id: "camp_001",
  companyName: "Acme Technologies",
  companyColor: "#3B82F6",
  companyInitials: "AT",
  jobPosition: "Senior Software Engineer",
  department: "Frontend Core",
  campaignName: "Acme Q3 Engineering Drive",
  practiceEnabled: true,
  interviewMode: "Technical",
  difficulty: "Hard",
  language: "English",
  voice: "Aditi (Indian English)",
  duration: "45 min",
  strategy: "Deep Dive into React & Distributed Systems",
  deadline: "2025-07-28",
  topics: ["React", "System Design", "Algorithms", "Behavioral"],
};

export const candidateJourney = {
  // Checklist statuses
  resumeUploaded: true,
  resumeAnalysed: true,
  internetStable: true,
  browserSupported: true,
  microphoneWorking: false, // Checked on interview page
  practiceCompleted: false,
  officialCompleted: false,
  reportGenerated: false,
  
  // Timeline events for Activity log
  activityTimeline: [
    { id: 1, title: "Invitation Received", description: "Invited by Acme Technologies", time: "3 days ago", completed: true },
    { id: 2, title: "Logged In", description: "First login to IntelliHire Portal", time: "2 days ago", completed: true },
    { id: 3, title: "Resume Uploaded", description: "Priya_Sharma_Resume.pdf", time: "2 days ago", completed: true },
    { id: 4, title: "Resume Analysed", description: "ATS Score: 95%", time: "2 days ago", completed: true },
    { id: 5, title: "Practice Completed", description: "Recommended before official", time: "Pending", completed: false },
    { id: 6, title: "Interview Started", description: "Official Session", time: "Pending", completed: false },
    { id: 7, title: "Interview Finished", description: "Awaiting AI Analysis", time: "Pending", completed: false },
    { id: 8, title: "Report Generated", description: "Sent to Hiring Manager", time: "Pending", completed: false },
  ],
  
  // Documents center
  documents: [
    { id: 1, name: "Priya_Sharma_Resume.pdf", type: "Resume", status: "Uploaded", date: "2 days ago" },
    { id: 2, name: "Interview Guidelines.pdf", type: "Company Document", status: "Available", date: "3 days ago" },
    { id: 3, name: "Data Processing Consent.pdf", type: "Consent", status: "Signed", date: "2 days ago" },
  ]
};

export const resumeData = {
  hasResume: true,
  fileName: "Priya_Sharma_Resume.pdf",
  fileSize: "284 KB",
  uploadedAt: "2025-07-10T10:30:00Z",
  status: "parsed",

  // Deep Resume Analysis (Not Interview Analysis)
  analysis: {
    overallScore: 88,
    atsCompatibility: 95,
    completeness: 100,
    roleMatchPercentage: 92,

    // High level metrics
    metrics: [
      { label: "Skill Coverage", value: 85, max: 100 },
      { label: "Experience Quality", value: 90, max: 100 },
      { label: "Project Quality", value: 82, max: 100 },
      { label: "Education Score", value: 95, max: 100 },
    ],

    // ATS Optimization tips
    tips: {
      improveAts: "Your formatting is excellent. Standardize date formats across all roles.",
      missingSkills: ["GraphQL", "CI/CD Pipelines", "Docker"],
      missingKeywords: ["Micro-frontends", "Performance Optimization"],
      grammarScore: 98,
      formattingScore: 95,
    },

    // Timeline for Resume page
    timeline: [
        { title: "Resume Uploaded", status: "done" },
        { title: "Resume Parsed", status: "done" },
        { title: "Skills Extracted", status: "done" },
        { title: "Projects Found", status: "done" },
        { title: "Experience Parsed", status: "done" },
        { title: "Ready for Interview", status: "done" },
    ],

    // Skills breakdown
    technicalSkills: ["React", "TypeScript", "Node.js", "Python", "MongoDB", "PostgreSQL", "AWS"],
    softSkills: ["Team Leadership", "Problem Solving", "Agile/Scrum", "Communication"],
    languages: ["English", "Hindi"],
    certifications: ["AWS Solutions Architect", "Meta React Developer"],

    radarData: [
      { subject: "Frontend", A: 90, fullMark: 100 },
      { subject: "Backend", A: 75, fullMark: 100 },
      { subject: "Architecture", A: 80, fullMark: 100 },
      { subject: "Cloud/DevOps", A: 60, fullMark: 100 },
      { subject: "Databases", A: 70, fullMark: 100 },
    ],

    strengths: [
      "Excellent coverage of modern frontend stack (React, TypeScript).",
      "Strong verifiable certifications from AWS and Meta.",
      "Good progression of responsibility in experience history."
    ],
    weakAreas: [
      "Limited mention of specific CI/CD pipelines.",
      "Backend architecture experience is slightly junior for a Senior role."
    ],
    aiSuggestions: [
      "Add metrics to your project descriptions (e.g., 'improved performance by 20%').",
      "Explicitly mention any microservices or distributed systems experience."
    ],
  },
};

export const interviewReportsData = {
  hasReport: false,
  overallScore: null,
  technicalScore: null,
  communicationScore: null,
  confidence: null,
  problemSolving: null,
  softSkills: null,
  timeManagement: null,
  resumeMatch: null,

  radarData: [],
  questionFeedback: [],
  strengths: [],
  weaknesses: [],
  companyRemarks: null,
  improvementSuggestions: [],
};

// Profile Interview History
export const interviewHistory = [
  { id: 1, type: "Practice Session", date: "2025-07-24", score: 75, status: "Completed", report: true },
  { id: 2, type: "Official Interview", date: "Pending", score: null, status: "Not Started", report: false }
];

export const faqData = [
  {
    id: "faq_001",
    question: "How does the AI Voice Interview work?",
    answer: "You will be connected to our AI system which acts as the interviewer. It will ask you questions based on the job role and dynamically adapt based on your answers. You will reply using your microphone.",
  },
  {
    id: "faq_002",
    question: "Can I pause the interview?",
    answer: "No, once the official interview starts, it cannot be paused. Ensure you are in a quiet environment with a stable internet connection.",
  },
  {
    id: "faq_003",
    question: "Who will see my report?",
    answer: "Your final interview report is shared directly with the hiring team at the company that invited you.",
  },
  {
    id: "faq_004",
    question: "Is practice mandatory?",
    answer: "If the company has enabled practice interviews for this campaign, we highly recommend taking one to familiarize yourself with the AI voice interaction before the official interview.",
  },
];

export const supportTickets = [];

export const interviewQuestions = [
  {
    id: "q_001",
    number: 1,
    text: "Tell me about yourself and your experience with React and frontend development.",
    topic: "Introduction",
    difficulty: "Easy",
    estimatedTime: "3 min",
  },
  {
    id: "q_002",
    number: 2,
    text: "Can you explain the difference between useState and useReducer in React? When would you use each?",
    topic: "React Hooks",
    difficulty: "Medium",
    estimatedTime: "4 min",
  },
  {
    id: "q_003",
    number: 3,
    text: "Describe a challenging project you worked on. What were the technical obstacles and how did you overcome them?",
    topic: "Problem Solving",
    difficulty: "Medium",
    estimatedTime: "5 min",
  },
];
