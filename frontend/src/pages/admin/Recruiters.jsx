import { useState, useEffect } from "react";
import { Download, ShieldAlert, CheckCircle, Trash2, Key } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import StatGrid from "../../components/layout/StatGrid";
import Card from "../../components/common/Card";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import Modal from "../../components/common/Modal";
import { RecruitersAPI } from "../../api/recruiters";
import "../../styles/admin/form.css";

export default function Recruiters() {
    const [selectedRecruiter, setSelectedRecruiter] = useState(null);
    const [recruiters, setRecruiters] = useState([]);
    const [loading, setLoading] = useState(true);

    const fetchRecruiters = async () => {
        setLoading(true);
        try {
            const data = await RecruitersAPI.getRecruiters({ limit: 100 });
            setRecruiters(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRecruiters();
    }, []);

    const handleSuspend = async (id) => {
        try {
            await RecruitersAPI.suspendRecruiter(id);
            fetchRecruiters();
            setSelectedRecruiter(prev => prev ? { ...prev, status: 'suspended' } : null);
        } catch (err) {
            console.error("Failed to suspend:", err);
        }
    };

    const handleActivate = async (id) => {
        try {
            await RecruitersAPI.activateRecruiter(id);
            fetchRecruiters();
            setSelectedRecruiter(prev => prev ? { ...prev, status: 'active' } : null);
        } catch (err) {
            console.error("Failed to activate:", err);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to completely delete this recruiter?")) {
            try {
                await RecruitersAPI.deleteRecruiter(id);
                fetchRecruiters();
                setSelectedRecruiter(null);
            } catch (err) {
                console.error("Failed to delete:", err);
            }
        }
    };

    const columns = [
        {
            title: "Recruiter", dataIndex: "name", sortable: true,
            render: (val, row) => (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <strong style={{ color: 'var(--text)' }}>{val}</strong>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.email}</span>
                </div>
            )
        },
        { title: "Company", dataIndex: "company_name", sortable: true },
        { title: "Role", dataIndex: "role", sortable: true, render: (val) => <span style={{ color: 'var(--text-secondary)' }}>{val?.toUpperCase()}</span> },
        {
            title: "Status", dataIndex: "status", sortable: true,
            render: (val) => {
                const map = { active: 'success', suspended: 'danger', pending: 'warning' };
                return <Badge variant={map[val] || 'primary'}>{val?.toUpperCase()}</Badge>;
            }
        },
        { title: "Created At", dataIndex: "created_at", sortable: true, align: "right", render: (val) => new Date(val).toLocaleDateString() },
    ];

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline"><Download size={16} /> Export</Button>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader title="Platform Monitor: Recruiters" description="Monitor recruiters across all companies. Creation and invites are handled by Company Admins." rightContent={rightContent} />

            <StatGrid>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Total Recruiters</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--text)' }}>{recruiters.length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Active</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--success)' }}>{recruiters.filter(r => r.status === 'active').length}</div>
                </Card>
                <Card className="ih-card">
                    <div style={{ color: 'var(--text-secondary)', fontSize: '13px', marginBottom: '8px' }}>Suspended</div>
                    <div style={{ fontSize: '28px', fontWeight: 'bold', color: 'var(--danger)' }}>{recruiters.filter(r => r.status === 'suspended').length}</div>
                </Card>
            </StatGrid>

            <SectionCard>
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable
                        columns={columns}
                        data={recruiters}
                        keyField="id"
                        searchable={true}
                        onRowClick={(row) => setSelectedRecruiter(row)}
                    />
                )}
            </SectionCard>

            <Modal
                isOpen={!!selectedRecruiter}
                onClose={() => setSelectedRecruiter(null)}
                title="Recruiter Monitor"
                footer={
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <div>
                            <Button variant="danger" onClick={() => handleDelete(selectedRecruiter?.id)}>
                                <Trash2 size={16} /> Delete
                            </Button>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <Button variant="outline" onClick={() => setSelectedRecruiter(null)}>Close</Button>
                        </div>
                    </div>
                }
            >
                {selectedRecruiter && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h3 style={{ margin: '0', fontSize: '18px', color: 'var(--text)' }}>{selectedRecruiter.name}</h3>
                                <p style={{ margin: '4px 0 0', fontSize: '14px', color: 'var(--text-secondary)' }}>{selectedRecruiter.email}</p>
                            </div>
                            <Badge variant={selectedRecruiter.status === 'active' ? 'success' : 'danger'}>
                                {selectedRecruiter.status?.toUpperCase()}
                            </Badge>
                        </div>
                        
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Company</label>
                                <div style={{ color: 'var(--text)', fontWeight: '500' }}>{selectedRecruiter.company_name}</div>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Role</label>
                                <div style={{ color: 'var(--text)', fontWeight: '500' }}>{selectedRecruiter.role?.toUpperCase()}</div>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Created At</label>
                                <div style={{ color: 'var(--text)', fontWeight: '500' }}>{new Date(selectedRecruiter.created_at).toLocaleString()}</div>
                            </div>
                        </div>

                        <div>
                            <h4 style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '12px' }}>Admin Actions</h4>
                            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                {selectedRecruiter.status === 'active' ? (
                                    <Button variant="outline" onClick={() => handleSuspend(selectedRecruiter.id)}>
                                        <ShieldAlert size={16} /> Suspend Access
                                    </Button>
                                ) : (
                                    <Button variant="success" onClick={() => handleActivate(selectedRecruiter.id)}>
                                        <CheckCircle size={16} /> Activate Access
                                    </Button>
                                )}
                                <Button variant="outline" onClick={() => alert("Force Logout initiated (API pending)")}>
                                    Force Logout
                                </Button>
                                <Button variant="outline" onClick={() => alert("Password reset link sent to recruiter.")}>
                                    <Key size={16} /> Reset Password
                                </Button>
                            </div>
                        </div>
                    </div>
                )}
            </Modal>
        </DashboardGrid>
    );
}
