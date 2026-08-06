import { useNavigate } from "react-router-dom";
import { Plus, Download, Filter } from "lucide-react";
import { useEffect, useState } from "react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import { CompaniesAPI } from "../../api/companies";

export default function Companies() {
    const navigate = useNavigate();
    const [companies, setCompanies] = useState([]);
    const [loading, setLoading] = useState(true);
    
    // Filters
    const [searchQuery, setSearchQuery] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [subscriptionFilter, setSubscriptionFilter] = useState("");
    const [showDeleted, setShowDeleted] = useState(false);

    const fetchCompanies = async () => {
        setLoading(true);
        try {
            const params = { limit: 100 };
            if (searchQuery) params.search = searchQuery;
            if (statusFilter) params.status = statusFilter;
            if (subscriptionFilter) params.subscription = subscriptionFilter;
            if (showDeleted) params.include_deleted = true;
            
            const data = await CompaniesAPI.getCompanies(params);
            setCompanies(data);
        } catch (err) {
            console.error("Failed to load companies:", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchCompanies();
    }, [searchQuery, statusFilter, subscriptionFilter, showDeleted]);

    const columns = [
        { 
            title: "Company ID", 
            dataIndex: "id", 
            sortable: true,
            render: (val) => <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{val?.substring(0, 8)}...</span>
        },
        { 
            title: "Company Name", 
            dataIndex: ["general", "name"], 
            sortable: true,
            render: (val, row) => <strong style={{ color: 'var(--text)' }}>{row.general?.name}</strong>
        },
        { 
            title: "Industry", 
            dataIndex: ["general", "industry"], 
            sortable: true,
            render: (val, row) => row.general?.industry || <span style={{ color: 'var(--text-muted)' }}>—</span>
        },
        { 
            title: "Plan", 
            dataIndex: ["subscription", "plan"], 
            sortable: true,
            render: (val, row) => row.subscription?.plan || "Basic"
        },
        { 
            title: "Status", 
            dataIndex: ["subscription", "status"],
            sortable: true,
            render: (val, row) => {
                let variant = 'primary';
                let displayVal = row.subscription?.status?.toUpperCase() || '—';
                if (row.deleted_at) {
                    variant = 'secondary';
                    displayVal = 'DELETED';
                } else {
                    if (row.subscription?.status === 'active') variant = 'success';
                    if (row.subscription?.status === 'suspended') variant = 'danger';
                    if (row.subscription?.status === 'pending') variant = 'warning';
                }
                return <Badge variant={variant}>{displayVal}</Badge>;
            }
        },
        { 
            title: "Max Campaigns", 
            dataIndex: ["limits", "max_campaigns"],
            sortable: true,
            align: "right",
            render: (val, row) => row.limits?.max_campaigns || 0
        }
    ];

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline">
                <Download size={16} />
                Export
            </Button>
            <Button variant="primary" onClick={() => navigate("/admin/companies/new")}>
                <Plus size={16} />
                Provision Company
            </Button>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader 
                title="Companies"
                description="Manage organizations, subscriptions, limits, and feature access."
                rightContent={rightContent}
            />

            <SectionCard>
                <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', alignItems: 'center' }}>
                    <div style={{ flex: 1 }}>
                        <input 
                            type="text" 
                            placeholder="Search by name, email, or industry..." 
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text)' }}
                        />
                    </div>
                    <select 
                        value={statusFilter} 
                        onChange={(e) => setStatusFilter(e.target.value)}
                        style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text)' }}
                    >
                        <option value="">All Statuses</option>
                        <option value="active">Active</option>
                        <option value="suspended">Suspended</option>
                        <option value="pending">Pending</option>
                    </select>
                    <select 
                        value={subscriptionFilter} 
                        onChange={(e) => setSubscriptionFilter(e.target.value)}
                        style={{ padding: '10px 16px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg-secondary)', color: 'var(--text)' }}
                    >
                        <option value="">All Plans</option>
                        <option value="Basic">Basic</option>
                        <option value="Professional">Professional</option>
                        <option value="Enterprise">Enterprise</option>
                    </select>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--text)', fontSize: '14px', cursor: 'pointer' }}>
                        <input 
                            type="checkbox" 
                            checked={showDeleted} 
                            onChange={(e) => setShowDeleted(e.target.checked)} 
                            style={{ width: '16px', height: '16px', accentColor: 'var(--primary)' }}
                        />
                        Show Deleted
                    </label>
                </div>

                {loading ? (
                    <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-secondary)' }}>Loading companies...</div>
                ) : (
                    <DataTable 
                        columns={columns} 
                        data={companies} 
                        keyField="id"
                        searchable={false}
                        onRowClick={(row) => navigate(`/admin/companies/${row.id}`)}
                    />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}