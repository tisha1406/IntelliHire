import { useState, useEffect } from "react";
import { Download, Filter } from "lucide-react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import DataTable from "../../components/common/DataTable";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import { SystemAPI } from "../../api/system";

export default function SecurityLogs() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchLogs = async () => {
            setLoading(true);
            try {
                const data = await SystemAPI.getSecurityLogs({ limit: 100 });
                setLogs(data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchLogs();
    }, []);

    const columns = [
        { 
            title: "Log ID", 
            dataIndex: "id", 
            sortable: true,
            render: (val) => <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{val}</span>
        },
        { 
            title: "Timestamp", 
            dataIndex: "timestamp", 
            sortable: true,
            render: (val) => <span style={{ color: 'var(--text-secondary)' }}>{new Date(val).toLocaleString()}</span>
        },
        { 
            title: "Severity", 
            dataIndex: "severity", 
            sortable: true,
            render: (val) => {
                let variant = 'primary';
                if (val === 'Critical' || val === 'High') variant = 'danger';
                if (val === 'Warning') variant = 'warning';
                if (val === 'Info') variant = 'primary';
                return <Badge variant={variant}>{val}</Badge>;
            }
        },
        { 
            title: "Event", 
            dataIndex: "event",
            sortable: true,
            render: (val) => <strong style={{ color: 'var(--text)' }}>{val}</strong>
        },
        { 
            title: "User", 
            dataIndex: "user",
            sortable: true
        },
        { 
            title: "IP Address", 
            dataIndex: "ip",
            sortable: true,
            render: (val) => <span style={{ fontFamily: 'monospace', color: 'var(--text-secondary)' }}>{val}</span>
        },
        { 
            title: "Status", 
            dataIndex: "status",
            sortable: true,
            render: (val) => {
                let variant = 'primary';
                if (val === 'Blocked' || val === 'Success' || val === 'Resolved') variant = 'success';
                if (val === 'Flagged' || val === 'Investigating' || val === 'Warning') variant = 'warning';
                if (val === 'Action Required') variant = 'danger';
                return <Badge variant={variant}>{val}</Badge>;
            }
        }
    ];

    const rightContent = (
        <div style={{ display: 'flex', gap: '12px' }}>
            <Button variant="outline">
                <Filter size={16} />
                Advanced Filters
            </Button>
            <Button variant="primary">
                <Download size={16} />
                Export CSV
            </Button>
        </div>
    );

    return (
        <DashboardGrid>
            <PageHeader 
                title="Security Logs"
                description="Audit trail for AI guardrails, anti-cheat events, and system anomalies."
                rightContent={rightContent}
            />

            <SectionCard>
                {loading ? <div style={{ padding: '24px', textAlign: 'center' }}>Loading...</div> : (
                    <DataTable 
                        columns={columns} 
                        data={logs} 
                        keyField="id"
                        searchable={true}
                        onRowClick={(row) => console.log("Expand log", row.id)}
                    />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}