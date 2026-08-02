import { useState, useEffect } from "react";
import { Download, ShieldAlert, CheckCircle, Trash2, Key, UserCog, LogOut } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import Modal from "../../components/common/Modal";
import { UsersAPI } from "../../api/users";

export default function Users() {
    const [activeTab, setActiveTab] = useState("all");
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedUser, setSelectedUser] = useState(null);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const data = await UsersAPI.getUsers({ limit: 100 });
            setUsers(data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleSuspend = async (id) => {
        try {
            await UsersAPI.suspendUser(id);
            fetchUsers();
            setSelectedUser(prev => prev ? { ...prev, status: 'suspended' } : null);
        } catch (err) {
            console.error("Failed to suspend user:", err);
        }
    };

    const handleActivate = async (id) => {
        try {
            await UsersAPI.activateUser(id);
            fetchUsers();
            setSelectedUser(prev => prev ? { ...prev, status: 'active' } : null);
        } catch (err) {
            console.error("Failed to activate user:", err);
        }
    };

    const handleDelete = async (id) => {
        if (window.confirm("Are you sure you want to delete this user?")) {
            try {
                await UsersAPI.deleteUser(id);
                fetchUsers();
                setSelectedUser(null);
            } catch (err) {
                console.error("Failed to delete user:", err);
            }
        }
    };

    const handleResetPassword = async (id) => {
        try {
            const res = await UsersAPI.resetPassword(id);
            alert(`Password Reset Successful!\n\nNew Temporary Password: ${res.temporary_password}\n\nPlease share this securely with the user.`);
        } catch (err) {
            alert("Failed to reset password.");
        }
    };

    const handleForceLogout = async (id) => {
        try {
            await UsersAPI.forceLogout(id);
            alert("User forced logout successfully.");
        } catch (err) {
            alert("Failed to force logout.");
        }
    };

    const handleRoleChange = async (id, newRole) => {
        try {
            await UsersAPI.updateRole(id, newRole);
            fetchUsers();
            setSelectedUser(prev => prev ? { ...prev, role: newRole } : null);
            alert("Role updated successfully.");
        } catch (err) {
            alert("Failed to update role.");
        }
    };

    const filteredUsers = users.filter(u => {
        const matchesTab = 
            activeTab === "all" || 
            (activeTab === "admin" && (u.role === "admin" || u.role === "support")) ||
            (activeTab === "company" && (u.role === "recruiter" || u.role === "company_admin"));
        return matchesTab;
    });

    const columns = [
        { 
            title: "Name", 
            dataIndex: "name", 
            sortable: true,
            render: (val, row) => (
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                    <strong style={{ color: 'var(--text)' }}>{val}</strong>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{row.email}</span>
                </div>
            )
        },
        { 
            title: "Role", 
            dataIndex: "role", 
            sortable: true,
            render: (val) => <span style={{ color: 'var(--text-secondary)' }}>{val?.toUpperCase()}</span>
        },
        { 
            title: "Status", 
            dataIndex: "status",
            sortable: true,
            render: (val) => {
                let variant = 'primary';
                let displayVal = val || 'Active';
                if (displayVal.toLowerCase() === 'active') variant = 'success';
                if (displayVal.toLowerCase() === 'suspended') variant = 'danger';
                return <Badge variant={variant}>{displayVal.toUpperCase()}</Badge>;
            }
        },
        { 
            title: "Last Login", 
            dataIndex: "last_login",
            sortable: true,
            render: (val) => <span style={{ color: 'var(--text-muted)' }}>{val ? new Date(val).toLocaleString() : 'Never'}</span>
        }
    ];

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline" onClick={fetchUsers}>
                <Download size={16} /> Export
            </Button>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader 
                title="Identity & Access Management"
                description="Manage platform administrators, roles, and global user access."
                rightContent={rightContent}
            />

            <SectionCard>
                <div style={{ display: 'flex', gap: '16px', borderBottom: '1px solid var(--border)', paddingBottom: '1px', marginBottom: '20px' }}>
                    <button 
                        style={{ 
                            background: 'transparent', border: 'none', cursor: 'pointer', padding: '8px 4px', 
                            color: activeTab === 'all' ? 'var(--text)' : 'var(--text-secondary)',
                            borderBottom: activeTab === 'all' ? '2px solid var(--primary)' : '2px solid transparent',
                            fontWeight: activeTab === 'all' ? '600' : '400',
                            fontSize: '14px'
                        }}
                        onClick={() => setActiveTab('all')}
                    >
                        All Users
                    </button>
                    <button 
                        style={{ 
                            background: 'transparent', border: 'none', cursor: 'pointer', padding: '8px 4px', 
                            color: activeTab === 'admin' ? 'var(--text)' : 'var(--text-secondary)',
                            borderBottom: activeTab === 'admin' ? '2px solid var(--primary)' : '2px solid transparent',
                            fontWeight: activeTab === 'admin' ? '600' : '400',
                            fontSize: '14px'
                        }}
                        onClick={() => setActiveTab('admin')}
                    >
                        Platform Admins
                    </button>
                    <button 
                        style={{ 
                            background: 'transparent', border: 'none', cursor: 'pointer', padding: '8px 4px', 
                            color: activeTab === 'company' ? 'var(--text)' : 'var(--text-secondary)',
                            borderBottom: activeTab === 'company' ? '2px solid var(--primary)' : '2px solid transparent',
                            fontWeight: activeTab === 'company' ? '600' : '400',
                            fontSize: '14px'
                        }}
                        onClick={() => setActiveTab('company')}
                    >
                        Company Users
                    </button>
                </div>
                
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable 
                        columns={columns} 
                        data={filteredUsers} 
                        keyField="id"
                        searchable={true}
                        onRowClick={(row) => setSelectedUser(row)}
                    />
                )}
            </SectionCard>

            <Modal
                isOpen={!!selectedUser}
                onClose={() => setSelectedUser(null)}
                title="IAM User Monitor"
                footer={
                    <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                        <div>
                            <Button variant="danger" onClick={() => handleDelete(selectedUser?.id)}>
                                <Trash2 size={16} /> Delete User
                            </Button>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <Button variant="outline" onClick={() => setSelectedUser(null)}>Close</Button>
                        </div>
                    </div>
                }
            >
                {selectedUser && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <div>
                                <h3 style={{ margin: '0', fontSize: '18px', color: 'var(--text)' }}>{selectedUser.name}</h3>
                                <p style={{ margin: '4px 0 0', fontSize: '14px', color: 'var(--text-secondary)' }}>{selectedUser.email}</p>
                            </div>
                            <Badge variant={(selectedUser.status || 'active').toLowerCase() === 'active' ? 'success' : 'danger'}>
                                {(selectedUser.status || 'active').toUpperCase()}
                            </Badge>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px' }}>
                            <div>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>Change Role</label>
                                <select 
                                    value={selectedUser.role} 
                                    onChange={(e) => handleRoleChange(selectedUser.id, e.target.value)}
                                    style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid var(--border)', background: 'var(--bg-primary)', color: 'var(--text)' }}
                                >
                                    <option value="admin">Platform Admin</option>
                                    <option value="support">Support</option>
                                    <option value="company_admin">Company Admin</option>
                                    <option value="recruiter">Recruiter</option>
                                </select>
                            </div>
                            <div>
                                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>Last Login</label>
                                <div style={{ color: 'var(--text)', fontWeight: '500' }}>
                                    {selectedUser.last_login ? new Date(selectedUser.last_login).toLocaleString() : 'Never'}
                                </div>
                            </div>
                        </div>

                        <div>
                            <h4 style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '12px' }}>Access Management</h4>
                            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                                {(selectedUser.status || 'active').toLowerCase() === 'active' ? (
                                    <Button variant="outline" onClick={() => handleSuspend(selectedUser.id)}>
                                        <ShieldAlert size={16} /> Suspend Access
                                    </Button>
                                ) : (
                                    <Button variant="success" onClick={() => handleActivate(selectedUser.id)}>
                                        <CheckCircle size={16} /> Activate Access
                                    </Button>
                                )}
                                <Button variant="outline" onClick={() => handleForceLogout(selectedUser.id)}>
                                    <LogOut size={16} /> Force Logout
                                </Button>
                                <Button variant="outline" onClick={() => handleResetPassword(selectedUser.id)}>
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
