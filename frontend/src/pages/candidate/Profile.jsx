import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import { User, Mail, Phone, Briefcase, Calendar, ShieldCheck, Camera, Building, History, ExternalLink, Check, Circle, Loader2 } from "lucide-react";
import { useCandidateProfile, useUpdateProfile } from "../../hooks/candidate/useCandidate";

const fadeUp = {
    hidden: { opacity: 0, y: 16 },
    show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.38, delay: i * 0.08 } }),
};

export default function Profile() {
    const { data: profile, isLoading } = useCandidateProfile();
    const { mutate: updateProfile, isPending } = useUpdateProfile();
    
    const [phone, setPhone] = useState("");
    const [isEditing, setIsEditing] = useState(false);

    useEffect(() => {
        if (profile) {
            setPhone(profile.phone || "");
        }
    }, [profile]);

    const handleSave = () => {
        updateProfile({ phone });
        setIsEditing(false);
    };

    if (isLoading) {
        return <div className="c-page" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}><Loader2 className="c-pulse-icon" /></div>;
    }

    return (
        <div className="c-page">
            <div className="c-page-header">
                <div>
                    <h1 className="c-page-title">Candidate Identity</h1>
                    <p className="c-page-subtitle">Your official profile for the {profile?.company_name} campaign.</p>
                </div>
            </div>

            <div className="c-two-col">
                {/* Left Column: Basic Info */}
                <motion.div custom={0} variants={fadeUp} initial="hidden" animate="show" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    <div className="c-card">
                        <div style={{ display: "flex", alignItems: "center", gap: 24, marginBottom: 24 }}>
                            <div style={{ position: "relative" }}>
                                <div style={{ width: 80, height: 80, borderRadius: "50%", background: "linear-gradient(135deg, #10B981, #059669)", display: "flex", alignItems: "center", justifyContent: "center", color: "white", fontSize: 32, fontWeight: 700 }}>
                                    {profile?.name?.charAt(0) || "U"}
                                </div>
                                <button style={{ position: "absolute", bottom: -4, right: -4, width: 32, height: 32, borderRadius: "50%", background: "var(--surface)", border: "1px solid var(--border)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text)", cursor: "pointer", transition: "all 0.2s" }}>
                                    <Camera size={14} />
                                </button>
                            </div>
                            <div>
                                <h2 style={{ fontSize: 20, fontWeight: 700, color: "var(--text)" }}>{profile?.name}</h2>
                                <p style={{ fontSize: 14, color: "var(--text-secondary)", marginBottom: 8 }}>Candidate Account</p>
                                <span className="c-tag" style={{ background: "rgba(59, 130, 246, 0.1)", color: "#3B82F6", borderColor: "rgba(59, 130, 246, 0.2)" }}>Member since {new Date(profile?.member_since).toLocaleDateString()}</span>
                            </div>
                        </div>

                        <div className="c-divider" style={{ margin: "16px 0" }} />

                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                                <div style={{ width: 36, height: 36, borderRadius: 8, background: "rgba(255,255,255,0.03)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-secondary)" }}><Mail size={16} /></div>
                                <div>
                                    <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Email Address</div>
                                    <div style={{ fontSize: 14, color: "var(--text)", fontWeight: 500 }}>{profile?.email}</div>
                                </div>
                            </div>
                            <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                                <div style={{ width: 36, height: 36, borderRadius: 8, background: "rgba(255,255,255,0.03)", display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text-secondary)" }}><Phone size={16} /></div>
                                <div style={{ flex: 1 }}>
                                    <div style={{ fontSize: 12, color: "var(--text-muted)", fontWeight: 600, textTransform: "uppercase" }}>Phone Number</div>
                                    {isEditing ? (
                                        <input 
                                            type="text" 
                                            value={phone} 
                                            onChange={(e) => setPhone(e.target.value)}
                                            style={{ background: 'var(--background)', border: '1px solid var(--border)', color: 'var(--text)', padding: '4px 8px', borderRadius: 4, width: '100%', fontSize: 14, marginTop: 4 }}
                                        />
                                    ) : (
                                        <div style={{ fontSize: 14, color: "var(--text)", fontWeight: 500 }}>{profile?.phone || "Not provided"}</div>
                                    )}
                                </div>
                            </div>
                        </div>
                        
                        <div style={{ marginTop: 24, display: "flex", justifyContent: "flex-end", gap: 12 }}>
                            {isEditing ? (
                                <>
                                    <button className="c-btn c-btn-secondary c-btn-sm" onClick={() => { setIsEditing(false); setPhone(profile?.phone || ""); }}>Cancel</button>
                                    <button className="c-btn c-btn-primary c-btn-sm" onClick={handleSave} disabled={isPending}>{isPending ? "Saving..." : "Save Changes"}</button>
                                </>
                            ) : (
                                <button className="c-btn c-btn-secondary c-btn-sm" onClick={() => setIsEditing(true)}>Edit Profile</button>
                            )}
                        </div>
                    </div>

                    <div className="c-card" style={{ background: "rgba(59, 130, 246, 0.02)", borderColor: "rgba(59, 130, 246, 0.1)" }}>
                        <div className="c-card-header">
                            <h3 className="c-card-title" style={{ display: "flex", alignItems: "center", gap: 8 }}><ShieldCheck size={18} color="#3B82F6" /> Account Security</h3>
                        </div>
                        <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, marginBottom: 16 }}>
                            Your interview data is securely encrypted and only shared with the hiring company. You can request data deletion at any time after the campaign ends.
                        </p>
                        <button className="c-btn c-btn-secondary c-btn-sm">Manage Security</button>
                    </div>
                </motion.div>

                {/* Right Column: Campaign Info & Interview History */}
                <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show" style={{ display: "flex", flexDirection: "column", gap: 24 }}>
                    <div className="c-card">
                        <div className="c-card-header">
                            <h3 className="c-card-title">Active Campaign Assignment</h3>
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                            <div className="c-info-row">
                                <span className="c-info-label"><Building size={14} style={{display:"inline", marginRight:4, verticalAlign:"middle"}}/> Company</span>
                                <span className="c-info-value">{profile?.company_name}</span>
                            </div>
                            <div className="c-info-row">
                                <span className="c-info-label"><Briefcase size={14} style={{display:"inline", marginRight:4, verticalAlign:"middle"}}/> Position</span>
                                <span className="c-info-value">{profile?.job_position}</span>
                            </div>
                            <div className="c-info-row">
                                <span className="c-info-label"><Calendar size={14} style={{display:"inline", marginRight:4, verticalAlign:"middle"}}/> Campaign Name</span>
                                <span className="c-info-value">{profile?.campaign_name}</span>
                            </div>
                        </div>
                    </div>

                    <div className="c-card">
                        <div className="c-card-header">
                            <h3 className="c-card-title" style={{ display: "flex", alignItems: "center", gap: 8 }}><History size={18} /> Interview History</h3>
                        </div>
                        
                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <div style={{fontSize: 12, color: "var(--text-muted)", padding: 12}}>No interview history available.</div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </div>
    );
}
