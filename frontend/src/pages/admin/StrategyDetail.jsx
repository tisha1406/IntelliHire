import { useParams, useNavigate } from "react-router-dom";
import { ArrowLeft, Edit } from "lucide-react";
import { useEffect, useState } from "react";
import toast, { Toaster } from "react-hot-toast";
import DashboardGrid from "../../layouts/DashboardGrid";
import PageHeader from "../../components/layout/PageHeader";
import SectionCard from "../../components/layout/SectionCard";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import DataTable from "../../components/common/DataTable";
import { StrategiesAPI } from "../../api/strategies";

function PolicyBlock({ title, data }) {
    if (!data) return null;
    return (
        <div style={{ marginBottom: "16px" }}>
            <h4 style={{ margin: "0 0 8px", fontSize: "13px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                {title}
            </h4>
            <pre
                style={{
                    margin: 0,
                    padding: "12px 16px",
                    borderRadius: "8px",
                    background: "var(--bg-secondary)",
                    border: "1px solid var(--border)",
                    color: "var(--text)",
                    fontSize: "13px",
                    overflowX: "auto",
                }}
            >
                {JSON.stringify(data, null, 2)}
            </pre>
        </div>
    );
}

export default function StrategyDetail() {
    const { strategyId } = useParams();
    const navigate = useNavigate();

    const [strategy, setStrategy] = useState(null);
    const [versions, setVersions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedVersion, setSelectedVersion] = useState(null);
    // Tracks which single version number currently has an activate/deactivate
    // request in flight, so only that row's button is disabled/shows a
    // spinner and a second click on the same row can't fire a duplicate request.
    const [activatingVersion, setActivatingVersion] = useState(null);

    const fetchData = async () => {
        setLoading(true);
        setError(null);
        try {
            const [latest, versionList] = await Promise.all([
                StrategiesAPI.getStrategy(strategyId),
                StrategiesAPI.getStrategyVersions(strategyId),
            ]);
            setStrategy(latest);
            const versionArray = Array.isArray(versionList) ? versionList : versionList?.data || [];
            setVersions(versionArray);
            setSelectedVersion(latest);
        } catch (err) {
            console.error("Failed to load strategy:", err);
            setError("Unable to load strategy details.");
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, [strategyId]);

    const handleSelectVersion = (row) => {
        setSelectedVersion(row);
    };

    // The backend is the sole authority over version state — this only
    // forwards the requested is_active flag via the real activation endpoint
    // and then re-fetches the strategy/version list so the UI reflects
    // whatever the backend actually persisted.
    const handleToggleActive = async (row, event) => {
        event.stopPropagation(); // don't also trigger the row's onRowClick (select-for-policy-view)
        if (activatingVersion !== null) return; // a request is already in flight; ignore extra clicks

        setActivatingVersion(row.version);
        try {
            await StrategiesAPI.activateVersion(strategyId, row.version, !row.is_active);
            toast.success(
                !row.is_active
                    ? `Version ${row.version} activated.`
                    : `Version ${row.version} deactivated.`
            );
            await fetchData();
        } catch (err) {
            console.error("Failed to update version activation status:", err);
            toast.error(err?.message || "Failed to update activation status.");
        } finally {
            setActivatingVersion(null);
        }
    };

    if (loading) {
        return (
            <DashboardGrid>
                <PageHeader title="Loading..." />
                <div style={{ padding: "20px", color: "var(--text-secondary)" }}>Loading strategy details...</div>
            </DashboardGrid>
        );
    }

    if (error) {
        return (
            <DashboardGrid>
                <PageHeader title="Error" />
                <div style={{ padding: "20px", display: "flex", flexDirection: "column", gap: "16px", alignItems: "flex-start" }}>
                    <span style={{ color: "var(--danger)" }}>{error}</span>
                    <Button variant="outline" onClick={fetchData}>Retry</Button>
                </div>
            </DashboardGrid>
        );
    }

    if (!strategy) {
        return (
            <DashboardGrid>
                <PageHeader title="Strategy Not Found" />
            </DashboardGrid>
        );
    }

    const versionColumns = [
        { title: "Version", dataIndex: "version", sortable: true, render: (val) => `v${val}` },
        {
            title: "Status",
            dataIndex: "is_active",
            render: (val) => <Badge variant={val ? "success" : "secondary"}>{val ? "ACTIVE" : "INACTIVE"}</Badge>,
        },
        {
            title: "Applicable Types",
            dataIndex: "applicable_interview_types",
            render: (val) =>
                Array.isArray(val) && val.length > 0 ? (
                    <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
                        {val.map((t) => (
                            <Badge key={t} variant="secondary">{t}</Badge>
                        ))}
                    </div>
                ) : (
                    <span style={{ color: "var(--text-muted)" }}>—</span>
                ),
        },
        {
            title: "Budget (min/target/max)",
            dataIndex: "target_questions",
            render: (val, row) => `${row.min_questions} / ${row.target_questions} / ${row.max_questions}`,
        },
        {
            title: "Created At",
            dataIndex: "created_at",
            // StrategyResponse (backend/app/schemas/admin.py) does not declare
            // created_at/updated_at fields, so the API never actually returns
            // them even though they're stored in Mongo — this intentionally
            // falls back to "—" rather than inventing a value.
            render: (val) => (val ? new Date(val).toLocaleString() : "—"),
        },
        {
            title: "Actions",
            dataIndex: "version",
            align: "right",
            render: (val, row) => (
                <Button
                    variant={row.is_active ? "outline" : "primary"}
                    size="sm"
                    isLoading={activatingVersion === row.version}
                    disabled={activatingVersion !== null && activatingVersion !== row.version}
                    onClick={(e) => handleToggleActive(row, e)}
                >
                    {row.is_active ? "Deactivate" : "Activate"}
                </Button>
            ),
        },
    ];

    const rightContent = (
        <div style={{ display: "flex", gap: "12px" }}>
            <Button variant="outline" onClick={() => navigate("/admin/strategies")}>
                <ArrowLeft size={16} /> Back to Strategies
            </Button>
            <Button variant="primary" onClick={() => navigate(`/admin/strategies/edit/${strategyId}`)}>
                <Edit size={16} /> Edit
            </Button>
        </div>
    );

    return (
        <DashboardGrid>
            <Toaster position="top-right" toastOptions={{ style: { background: "var(--card-bg)", color: "var(--text)", border: "1px solid var(--border)" } }} />

            <PageHeader
                title={strategy.name}
                description={strategy.description}
                rightContent={rightContent}
            />

            <SectionCard>
                <div style={{ display: "flex", gap: "24px", flexWrap: "wrap" }}>
                    <div>
                        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Strategy ID</span>
                        <div style={{ fontFamily: "monospace", color: "var(--text)" }}>{strategy.strategy_id}</div>
                    </div>
                    <div>
                        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Latest Version</span>
                        <div style={{ color: "var(--text)" }}>v{strategy.version}</div>
                    </div>
                    <div>
                        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Status</span>
                        <div>
                            <Badge variant={strategy.is_active ? "success" : "secondary"}>
                                {strategy.is_active ? "ACTIVE" : "INACTIVE"}
                            </Badge>
                        </div>
                    </div>
                    <div>
                        <span style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Applicable Types</span>
                        <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                            {(strategy.applicable_interview_types || []).map((t) => (
                                <Badge key={t} variant="secondary">{t}</Badge>
                            ))}
                        </div>
                    </div>
                </div>
            </SectionCard>

            <SectionCard>
                <h3 style={{ marginTop: 0 }}>Version History</h3>
                <DataTable
                    columns={versionColumns}
                    data={versions}
                    keyField="version"
                    searchable={false}
                    pagination={false}
                    onRowClick={handleSelectVersion}
                    emptyState={
                        <div style={{ padding: "16px", textAlign: "center", color: "var(--text-secondary)" }}>
                            No version history found.
                        </div>
                    }
                />
            </SectionCard>

            <SectionCard>
                <h3 style={{ marginTop: 0 }}>
                    Policy Detail {selectedVersion ? `— v${selectedVersion.version}` : ""}
                </h3>
                <PolicyBlock title="Topic Selection Policy" data={selectedVersion?.topic_selection_policy} />
                <PolicyBlock title="Difficulty Policy" data={selectedVersion?.difficulty_policy} />
                <PolicyBlock title="Follow-up Policy" data={selectedVersion?.followup_policy} />
                <PolicyBlock title="Gap Policy" data={selectedVersion?.gap_policy} />
                <PolicyBlock title="Completion Policy" data={selectedVersion?.completion_policy} />
                <PolicyBlock title="Company Override Bounds" data={selectedVersion?.company_override_bounds} />
                <PolicyBlock
                    title="Thresholds"
                    data={
                        selectedVersion && {
                            weak_threshold: selectedVersion.weak_threshold,
                            acceptable_threshold: selectedVersion.acceptable_threshold,
                            strong_threshold: selectedVersion.strong_threshold,
                        }
                    }
                />
            </SectionCard>
        </DashboardGrid>
    );
}
