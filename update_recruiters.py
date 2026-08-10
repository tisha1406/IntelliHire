import re

with open(r"d:\Sem 5\SGP\IntelliHire\frontend\src\pages\company\Recruiters.jsx", "r", encoding="utf-8") as f:
    content = f.read()

# Add campaignService import
content = content.replace(
    'import recruiterManagementService from "../../services/company/recruiterManagementService";',
    'import recruiterManagementService from "../../services/company/recruiterManagementService";\nimport campaignService from "../../services/company/campaignService";'
)

# Add state variables
content = content.replace(
    'const [toast, setToast] = useState(null);',
    'const [toast, setToast] = useState(null);\n    const [assignModal, setAssignModal] = useState(null);\n    const [campaigns, setCampaigns] = useState([]);\n    const [selectedCampaigns, setSelectedCampaigns] = useState([]);'
)

# Add loadCampaigns to useEffect
content = content.replace(
    'loadRecruiters();\n    }, []);',
    'loadRecruiters();\n        loadCampaigns();\n    }, []);\n\n    const loadCampaigns = async () => {\n        try {\n            const res = await campaignService.getCampaigns();\n            setCampaigns(res.data?.data || res.data || []);\n        } catch (err) {\n            console.error(err);\n        }\n    };'
)

# Add assign campaigns handler
assign_handler = """
    const handleOpenAssign = async (recruiter) => {
        try {
            const res = await recruiterManagementService.getRecruiterCampaigns(recruiter.id);
            const assigned = (res.data?.data || res.data || []).map(c => c._id);
            setSelectedCampaigns(assigned);
            setAssignModal(recruiter);
        } catch (err) {
            showToast("Failed to load recruiter campaigns", "error");
        }
    };

    const handleSaveAssign = async () => {
        try {
            await recruiterManagementService.updateRecruiterCampaigns(assignModal.id, selectedCampaigns);
            showToast("Campaigns assigned successfully", "success");
            setAssignModal(null);
        } catch (err) {
            showToast("Failed to assign campaigns", "error");
        }
    };
"""

content = content.replace('const filtered = recruiters.filter(', assign_handler + '\n    const filtered = recruiters.filter(')

# Update table headers
content = content.replace(
    '<th style={{ padding: "16px", fontWeight: 600 }}>Status</th>',
    '<th style={{ padding: "16px", fontWeight: 600 }}>Status</th>\n                                    <th style={{ padding: "16px", fontWeight: 600 }}>Last Login</th>'
)

# Update table row
row_update = """                                        <td style={{ padding: "16px" }}>
                                            <StatusBadge status={r.account_status || r.status || "Active"} />
                                        </td>
                                        <td style={{ padding: "16px", color: "var(--text-secondary)", fontSize: 13 }}>
                                            {r.last_login ? new Date(r.last_login).toLocaleDateString() : "Never"}
                                        </td>
                                        <td style={{ padding: "16px", textAlign: "right" }}>
                                            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
                                                <button onClick={() => handleOpenAssign(r)} style={{ background: "none", border: "none", color: "var(--primary)", cursor: "pointer", padding: 6 }} title="Assign Campaigns"><FaUserPlus /></button>"""

content = content.replace(
    '<td style={{ padding: "16px" }}>\n                                            <StatusBadge status={r.status} />\n                                        </td>\n                                        <td style={{ padding: "16px", textAlign: "right" }}>\n                                            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>',
    row_update
)

# Add assign modal UI
modal_ui = """
                {assignModal && (
                    <div style={{
                        position: "fixed", top: 0, left: 0, right: 0, bottom: 0,
                        background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000
                    }}>
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
                            style={{
                                background: "var(--card)", padding: 32, borderRadius: "var(--radius-lg)",
                                width: "100%", maxWidth: 500, border: "1px solid var(--border)", boxShadow: "0 20px 40px rgba(0,0,0,0.2)"
                            }}
                        >
                            <h2 style={{ marginBottom: 8, fontSize: 20, color: "var(--text)", fontWeight: 700 }}>Assign Campaigns</h2>
                            <p style={{ color: "var(--text-secondary)", marginBottom: 24, fontSize: 14 }}>
                                Select campaigns for {assignModal.first_name} {assignModal.last_name}. They will only have access to these selected campaigns.
                            </p>
                            
                            <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 24, border: "1px solid var(--border)", borderRadius: "var(--radius-md)" }}>
                                {campaigns.map(c => (
                                    <div key={c._id} style={{ 
                                        display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", 
                                        borderBottom: "1px solid var(--border)", cursor: "pointer",
                                        background: selectedCampaigns.includes(c._id) ? "rgba(16, 185, 129, 0.05)" : "transparent"
                                    }} onClick={() => {
                                        if (selectedCampaigns.includes(c._id)) {
                                            setSelectedCampaigns(selectedCampaigns.filter(id => id !== c._id));
                                        } else {
                                            setSelectedCampaigns([...selectedCampaigns, c._id]);
                                        }
                                    }}>
                                        <input 
                                            type="checkbox" 
                                            checked={selectedCampaigns.includes(c._id)} 
                                            onChange={() => {}}
                                            style={{ cursor: "pointer", width: 16, height: 16 }}
                                        />
                                        <div>
                                            <div style={{ fontWeight: 500, color: "var(--text)" }}>{c.name || c.title || "Untitled"}</div>
                                            <div style={{ fontSize: 12, color: "var(--text-muted)" }}>{c.department} &bull; {c.status}</div>
                                        </div>
                                    </div>
                                ))}
                                {campaigns.length === 0 && (
                                    <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)" }}>No campaigns available.</div>
                                )}
                            </div>
                            
                            <div style={{ display: "flex", gap: 12, justifyContent: "flex-end" }}>
                                <Button variant="outline" onClick={() => setAssignModal(null)}>Cancel</Button>
                                <Button variant="primary" onClick={handleSaveAssign}>Save Assignments</Button>
                            </div>
                        </motion.div>
                    </div>
                )}
"""

content = content.replace('            </AnimatePresence>\n        </div>', modal_ui + '\n            </AnimatePresence>\n        </div>')

with open(r"d:\Sem 5\SGP\IntelliHire\frontend\src\pages\company\Recruiters.jsx", "w", encoding="utf-8") as f:
    f.write(content)
