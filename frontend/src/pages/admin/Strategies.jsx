import { useNavigate } from "react-router-dom";
import { Plus } from "lucide-react";
import { useEffect, useState } from "react";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import DataTable from "../../components/common/DataTable";
import Badge from "../../components/common/Badge";
import Button from "../../components/common/Button";
import { StrategiesAPI } from "../../api/strategies";

export default function Strategies() {
    const navigate = useNavigate();
    const [strategies, setStrategies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const fetchStrategies = async () => {
        setLoading(true);
        setError(null);
        try {
            const data = await StrategiesAPI.getStrategies({ limit: 100 });
            setStrategies(Array.isArray(data) ? data : data?.data || []);
        } catch (err) {
            console.error("Failed to load strategies:", err);
            setError("Unable to load strategies.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStrategies();
    }, []);

    const columns = [
        {
            title: "Strategy ID",
            dataIndex: "strategy_id",
            sortable: true,
            render: (val) => <span style={{ fontFamily: "monospace", color: "var(--text)" }}>{val}</span>,
        },
        {
            title: "Name",
            dataIndex: "name",
            sortable: true,
            render: (val) => <strong style={{ color: "var(--text)" }}>{val}</strong>,
        },
        {
            title: "Applicable Types",
            dataIndex: "applicable_interview_types",
            render: (val) =>
                Array.isArray(val) && val.length > 0 ? (
                    <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        {val.map((t) => (
                            <Badge key={t} variant="secondary">{t}</Badge>
                        ))}
                    </div>
                ) : (
                    <span style={{ color: "var(--text-muted)" }}>—</span>
                ),
        },
        {
            title: "Latest Version",
            dataIndex: "version",
            sortable: true,
            align: "right",
            render: (val) => <span>v{val}</span>,
        },
        {
            title: "Status",
            dataIndex: "is_active",
            sortable: true,
            render: (val) => (
                <Badge variant={val ? "success" : "secondary"}>{val ? "ACTIVE" : "INACTIVE"}</Badge>
            ),
        },
        {
            title: "Budget (min/target/max)",
            dataIndex: "target_questions",
            render: (val, row) => `${row.min_questions} / ${row.target_questions} / ${row.max_questions}`,
        },
    ];

    return (
        <DashboardGrid>
            <PageHeader
                title="Interview Strategies"
                description="View and author Admin-published strategy definitions. Version creation and activation are added in a follow-up task."
                rightContent={
                    <Button variant="primary" onClick={() => navigate("/admin/strategies/new")}>
                        <Plus size={16} /> New Strategy
                    </Button>
                }
            />

            <SectionCard>
                {loading ? (
                    <div style={{ padding: "24px", textAlign: "center", color: "var(--text-secondary)" }}>
                        Loading strategies...
                    </div>
                ) : error ? (
                    <div style={{ padding: "24px", color: "var(--danger)" }}>{error}</div>
                ) : (
                    <DataTable
                        columns={columns}
                        data={strategies}
                        keyField="strategy_id"
                        searchable={false}
                        emptyState={
                            <div style={{ padding: "24px", textAlign: "center", color: "var(--text-secondary)" }}>
                                No strategies found.
                            </div>
                        }
                        onRowClick={(row) => navigate(`/admin/strategies/${row.strategy_id}`)}
                    />
                )}
            </SectionCard>
        </DashboardGrid>
    );
}
