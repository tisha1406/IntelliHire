import { useState } from "react";
import { motion } from "framer-motion";
import { UploadCloud, FileText, CheckCircle2, AlertTriangle, Zap, Check, Clock, Loader2 } from "lucide-react";
import { useResumeStatus, useResumeAnalysis, useUploadResume } from "../../hooks/candidate/useCandidate";
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from "recharts";
import "../../styles/candidate/resume.css";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Resume() {
    const [isDragging, setIsDragging] = useState(false);
    
    const { data: statusData, isLoading: statusLoading } = useResumeStatus();
    const { data: analysisData, isLoading: analysisLoading } = useResumeAnalysis();
    const { mutate: uploadResume, isPending: isUploading } = useUploadResume();

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setIsDragging(true);
        } else if (e.type === "dragleave") {
            setIsDragging(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
        
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    };
    
    const handleFileSelect = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    };
    
    const handleFile = (file) => {
        if (file.size > 5 * 1024 * 1024) {
            alert("File size must be under 5MB");
            return;
        }
        uploadResume(file);
    };

    if (statusLoading) return <div className="c-page">Loading...</div>;

    const hasResume = statusData?.has_resume;
    const status = statusData?.status;

    return (
        <div className="c-page">
            <div className="c-page-header">
                <div>
                    <h1 className="c-page-title">Resume Analysis</h1>
                    <p className="c-page-subtitle">Upload your resume to see how it matches with the role.</p>
                </div>
            </div>

            {/* Upload Area */}
            <motion.div initial="hidden" animate="show" variants={fadeUp} custom={0}>
                {!hasResume ? (
                    <div 
                        className={`c-resume-upload ${isDragging ? "drag-active" : ""}`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <div className="c-upload-icon">
                            {isUploading ? <Loader2 size={32} className="c-pulse-icon" /> : <UploadCloud size={32} />}
                        </div>
                        <h3 className="c-upload-title">{isUploading ? "Uploading & Analyzing..." : "Drag & Drop your resume here"}</h3>
                        <p className="c-upload-desc">Supported formats: PDF, DOCX (Max size: 5MB). We will automatically parse and analyze it against the campaign requirements.</p>
                        
                        <input 
                            type="file" 
                            id="resume-upload" 
                            style={{ display: "none" }} 
                            accept=".pdf,.docx,.doc"
                            onChange={handleFileSelect}
                            disabled={isUploading}
                        />
                        <button 
                            className="c-upload-btn" 
                            onClick={() => document.getElementById("resume-upload").click()}
                            disabled={isUploading}
                        >
                            Browse Files
                        </button>
                    </div>
                ) : (
                    <div className="c-file-info">
                        <div className="c-file-details">
                            <div className="c-file-icon">
                                {status === "processing" ? <Loader2 size={24} className="c-pulse-icon" /> : <FileText size={24} />}
                            </div>
                            <div>
                                <div className="c-file-name">Resume Uploaded</div>
                                <div className="c-file-meta">
                                    Uploaded {new Date(statusData.uploaded_at).toLocaleDateString()}
                                    {status === "processing" && " • Analyzing..."}
                                </div>
                            </div>
                        </div>
                        <div className="c-page-actions">
                            <input 
                                type="file" 
                                id="resume-replace" 
                                style={{ display: "none" }} 
                                accept=".pdf,.docx,.doc"
                                onChange={handleFileSelect}
                            />
                            <button className="c-btn c-btn-secondary c-btn-sm" onClick={() => document.getElementById("resume-replace").click()}>Replace</button>
                        </div>
                    </div>
                )}
            </motion.div>

            {hasResume && status === "analysed" && analysisData && (
                <div className="c-resume-grid">
                    
                    {/* Overall Match */}
                    <motion.div className="c-card col-span-8" initial="hidden" animate="show" variants={fadeUp} custom={1}>
                        <div className="c-card-header">
                            <h3 className="c-card-title">Role Compatibility</h3>
                        </div>
                        <div className="c-score-ring-container">
                            <div className="c-score-ring">
                                <div className="c-ring-circle success">{analysisData.ats_score}%</div>
                                <div className="c-ring-label">ATS Score</div>
                            </div>
                            <div className="c-score-ring">
                                <div className="c-ring-circle success">{analysisData.role_match}%</div>
                                <div className="c-ring-label">Role Match</div>
                            </div>
                            <div className="c-score-ring">
                                <div className="c-ring-circle">{analysisData.overall_score}%</div>
                                <div className="c-ring-label">Overall Strength</div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Resume Timeline (NEW for B2B) */}
                    <motion.div className="c-card col-span-4" initial="hidden" animate="show" variants={fadeUp} custom={2}>
                        <div className="c-card-header">
                            <h3 className="c-card-title">Resume Processing</h3>
                        </div>
                        <div className="c-resume-timeline">
                            {analysisData.timeline.map((step, i) => (
                                <div key={i} className={`c-r-time-item ${step.status === "done" ? "done" : ""}`}>
                                    <div className="c-r-time-icon">
                                        {step.status === "done" ? <Check size={14} /> : <Clock size={14} />}
                                    </div>
                                    <span className="c-r-time-text">{step.title}</span>
                                </div>
                            ))}
                        </div>
                    </motion.div>

                    {/* Skill Radar */}
                    <motion.div className="c-card col-span-4" initial="hidden" animate="show" variants={fadeUp} custom={3}>
                        <div className="c-card-header">
                            <h3 className="c-card-title">Skill Distribution</h3>
                        </div>
                        <div style={{ width: "100%", height: 260 }}>
                            <ResponsiveContainer width="100%" height="100%">
                                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={analysisData.radar_data}>
                                    <PolarGrid stroke="var(--border)" />
                                    <PolarAngleAxis dataKey="subject" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} />
                                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                                    <Radar name="Candidate" dataKey="A" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.4} />
                                </RadarChart>
                            </ResponsiveContainer>
                        </div>
                    </motion.div>

                    {/* Detected Skills */}
                    <motion.div className="c-card col-span-4" initial="hidden" animate="show" variants={fadeUp} custom={4}>
                        <div className="c-card-header">
                            <h3 className="c-card-title">Detected Skills</h3>
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Technical</span>
                            <div className="c-tags-list">
                                {analysisData.technical_skills.map((s, i) => <span key={i} className="c-tag">{s}</span>)}
                            </div>
                        </div>
                        <div>
                            <span style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Soft Skills & Certs</span>
                            <div className="c-tags-list">
                                {analysisData.soft_skills.map((s, i) => <span key={i} className="c-tag" style={{ background: "rgba(139, 92, 246, 0.1)", borderColor: "rgba(139, 92, 246, 0.2)", color: "#A78BFA" }}>{s}</span>)}
                            </div>
                        </div>
                    </motion.div>

                    {/* Resume Optimization Tips (NEW for B2B) */}
                    <motion.div className="c-card col-span-4" initial="hidden" animate="show" variants={fadeUp} custom={5}>
                        <div className="c-card-header">
                            <h3 className="c-card-title">Optimization Tips</h3>
                        </div>
                        
                        <div className="c-tip-box">
                            <div className="c-tip-title">ATS Format Improvement</div>
                            <div className="c-tip-text">{analysisData.improve_ats}</div>
                        </div>
                        
                        <div style={{ marginBottom: 16 }}>
                            <span style={{ fontSize: 12, color: "var(--danger)", fontWeight: 600, textTransform: "uppercase", marginBottom: 4, display: "block" }}>Missing Requirements</span>
                            <div className="c-tags-list">
                                {analysisData.missing_keywords.map((s, i) => <span key={i} className="c-tag" style={{ background: "rgba(239, 68, 68, 0.05)", borderColor: "rgba(239, 68, 68, 0.2)", color: "#EF4444" }}>{s}</span>)}
                            </div>
                        </div>

                        <div style={{ display: "flex", gap: 16 }}>
                            <div style={{ flex: 1, padding: 12, background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)" }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Grammar</div>
                                <div style={{ fontSize: 18, fontWeight: 700, color: "var(--success)" }}>{analysisData.grammar_score}%</div>
                            </div>
                            <div style={{ flex: 1, padding: 12, background: "var(--surface)", borderRadius: 8, border: "1px solid var(--border)" }}>
                                <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Formatting</div>
                                <div style={{ fontSize: 18, fontWeight: 700, color: "var(--success)" }}>{analysisData.formatting_score}%</div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            )}
        </div>
    );
}
