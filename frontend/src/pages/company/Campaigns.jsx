export default function Campaigns() { return null; }
import React, { useState } from "react";
import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { FaPlus, FaTh, FaList, FaSearch, FaTimesCircle, FaPlusCircle } from "react-icons/fa";

import campaignService from "../../services/company/campaignService";

// Reusable components
import PageHeader from "../../components/common/PageHeader";
import CampaignCard from "../../components/common/CampaignCard";
import SearchBar from "../../components/common/SearchBar";
import FilterDropdown from "../../components/common/FilterDropdown";
import Tabs from "../../components/common/Tabs";
import ConfirmDialog from "../../components/common/ConfirmDialog";
import Toast from "../../components/common/Toast";
import EmptyState from "../../components/common/EmptyState";
import Button from "../../components/common/Button";

import "../../styles/company/Campaign.css";

export default function Campaigns() {
    const navigate = useNavigate();

    // Local Campaign list state
    const [campaigns, setCampaigns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedDept, setSelectedDept] = useState("");
    const [activeTab, setActiveTab] = useState("all");
    const [layout, setLayout] = useState("grid"); // grid or list

    // Modal/Dialog states
    const [deleteId, setDeleteId] = useState(null);
    const [isConfirmOpen, setIsConfirmOpen] = useState(false);

    // Toast Notification states
    const [toastMessage, setToastMessage] = useState(null);
    const [toastType, setToastType] = useState("success");

    const triggerToast = (msg, type = "success") => {
        setToastMessage(msg);
        setToastType(type);
    };

    // Filter Options
    const departments = [
        { value: "Engineering", label: "Engineering" },
        { value: "AI & Data Science", label: "AI & Data Science" },
        { value: "Design", label: "Design" },
        { value: "Product", label: "Product" },
        { value: "Marketing", label: "Marketing" },
        { value: "Sales", label: "Sales" },
        { value: "Human Resources", label: "Human Resources" }
    ];

    const statusTabs = [
        { id: "all", label: "All Campaigns" },
        { id: "active", label: "Active" },
        { id: "draft", label: "Draft" },
        { id: "closed", label: "Closed" },
        { id: "scheduled", label: "Scheduled" }
    ];

    // Actions
const handleDuplicate = async (id) => {
    try {

        const res = await campaignService.getCampaign(id);

        const target = res.data;

        const payload = {
            company_id: target.company_id,
            name: `${target.name} (Copy)`,
            department: target.department,
            location: target.location,
            deadline: target.deadline,
            salary: target.salary,
            description: target.description,
            employment_type: target.employment_type,
            requirements: target.requirements,
            interview_settings: target.interview_settings
        };

        await campaignService.createCampaign(payload);

        fetchCampaigns();

        triggerToast("Campaign duplicated successfully");

    } catch (err) {

        console.error(err);

        triggerToast("Duplicate failed", "error");
    }
};

    const handleDeleteClick = (id) => {
    console.log("Delete clicked:", id);
    setDeleteId(id);
    setIsConfirmOpen(true);
};

    const handleConfirmDelete = async () => {

        console.log("Confirm delete:", deleteId);

    try {
        console.log("Calling delete API...");
        await campaignService.deleteCampaign(deleteId);

        await fetchCampaigns();

        triggerToast("Campaign deleted successfully");

    } catch (err) {

        console.error(err);

        triggerToast("Failed to delete campaign", "error");

    } finally {

        setDeleteId(null);

        setIsConfirmOpen(false);

    }
};

    const handleEdit = (id) => {
        navigate(`/company/campaigns/edit/${id}`);
    };
    const handleView = (id) => {
        navigate(`/company/campaigns/${id}`);
    };

    // Filter Logic
    const filteredCampaigns = campaigns.filter((camp) => {
        const search = searchQuery.toLowerCase();

        const matchesSearch =
            (camp.name || "").toLowerCase().includes(search) ||
            (camp.recruiter || "").toLowerCase().includes(search) ||
            (camp.department || "").toLowerCase().includes(search);

        const matchesDept = selectedDept === "" || camp.department === selectedDept;

        const matchesStatus = activeTab === "all" || (camp.status || "").toLowerCase() === activeTab;

        return matchesSearch && matchesDept && matchesStatus;
    });

    const fetchCampaigns = async () => {

        try {

            setLoading(true);

            const res = await campaignService.getCampaigns();

            const campaigns = res.data.map(c => ({

                ...c,

                id: c._id

            }));

            setCampaigns(campaigns);

        } catch (err) {

            console.error(err);

            triggerToast("Unable to load campaigns", "error");

        } finally {

            setLoading(false);

        }

    };

    useEffect(() => {

        fetchCampaigns();

    }, []);

    if (loading) {

        return (

            <div className="loading-page">

                Loading Campaigns...

            </div>

        );

    }

    return (
        <div className="campaigns-page-container">
            <PageHeader
                title="Hiring Campaigns"
                subtitle="Manage hiring campaigns."
                breadcrumbs={[{ label: "Campaigns" }]}
                actions={
                    <Button variant="primary" iconLeft={<FaPlus />} onClick={() => navigate("/company/campaigns/new")}>
                        Create Campaign
                    </Button>
                }
            />

            {/* Filter controls */}
            <div className="campaigns-filter-bar">
                <div className="filter-left">
                    <SearchBar
                        value={searchQuery}
                        onChange={setSearchQuery}
                        placeholder="Search by title, recruiter..."
                    />
                    <FilterDropdown
                        label="Department"
                        options={departments}
                        selected={selectedDept}
                        onChange={setSelectedDept}
                    />
                </div>

                <div className="filter-right">
                    <div className="layout-toggle-group">
                        <button
                            className={`toggle-layout-btn ${layout === "grid" ? "is-active" : ""}`}
                            onClick={() => setLayout("grid")}
                            title="Grid Layout"
                        >
                            <FaTh />
                        </button>
                        <button
                            className={`toggle-layout-btn ${layout === "list" ? "is-active" : ""}`}
                            onClick={() => setLayout("list")}
                            title="List Layout"
                        >
                            <FaList />
                        </button>
                    </div>
                </div>
            </div>

            {/* Status tabs */}
            <Tabs
                tabs={statusTabs}
                activeTab={activeTab}
                onChange={setActiveTab}
                className="campaigns-status-tabs"
            />

            {/* Campaign lists container */}
            <div className="campaigns-content-area">
                {filteredCampaigns.length === 0 ? (
                    <EmptyState
                        title="No campaigns found"
                        description="Try resetting your active tab, search filters, or create a brand new campaign template."
                        action={
                            <Button variant="outline" onClick={() => { setSearchQuery(""); setSelectedDept(""); setActiveTab("all"); }}>
                                Reset Filters
                            </Button>
                        }
                    />
                ) : (
                    <motion.div
                        className={layout === "grid" ? "campaigns-cards-grid" : "campaigns-cards-list"}
                        layout
                    >
                        <AnimatePresence mode="popLayout">
                            {filteredCampaigns.map((camp) => (
                                <CampaignCard
                                    key={camp.id}
                                    campaign={camp}
                                    layout={layout}
                                    onView={() => handleView(camp.id)}
                                    onEdit={() => handleEdit(camp.id)}
                                    onDuplicate={() => handleDuplicate(camp.id)}
                                    onDelete={() => handleDeleteClick(camp.id)}
                                />
                            ))}
                        </AnimatePresence>
                    </motion.div>
                )}
            </div>



            {/* Delete Confirmation Modal */}
            <ConfirmDialog
                isOpen={isConfirmOpen}
                onClose={() => setIsConfirmOpen(false)}
                onConfirm={handleConfirmDelete}
                title="Delete Campaign"
                message="Are you absolutely sure you want to delete this hiring campaign? This will permanently close candidate portals."
            />

            {/* Toast Alerts — fixed top-right, slides in from top */}
            <AnimatePresence>
                {toastMessage && (
                    <>
                        {/* Backdrop blur overlay */}
                        <motion.div
                            className="toast-backdrop"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            onClick={() => setToastMessage(null)}
                        />
                        {/* Toast notification */}
                        <div className="toast-portal">
                            <Toast
                                message={toastMessage}
                                type={toastType}
                                onClose={() => setToastMessage(null)}
                            />
                        </div>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
}
